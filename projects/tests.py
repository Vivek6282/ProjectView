import os
from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.models import UserProfile
from projects.models import Project, ProjectAsset
from datetime import date, timedelta


class ProjectPermissionsAndUploadTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(username='mgr', password='pwd')
        self.manager.profile.role = 'manager'
        self.manager.profile.save()

        self.hr = User.objects.create_user(username='hr_user', password='pwd')
        self.hr.profile.role = 'hr'
        self.hr.profile.save()

        self.employee = User.objects.create_user(username='emp', password='pwd')
        self.employee.profile.role = 'employee'
        self.employee.profile.save()

        self.employee_creator = User.objects.create_user(username='emp_creator', password='pwd')
        self.employee_creator.profile.role = 'employee'
        self.employee_creator.profile.save()

        self.staff = User.objects.create_user(username='staff_user', password='pwd', is_staff=True)
        self.staff.profile.role = 'employee'
        self.staff.profile.save()

        # Project created by manager
        self.mgr_project = Project.objects.create(
            title='Manager Project',
            category='Web Development',
            deadline=date.today() + timedelta(days=7),
            status='In Progress',
            created_by=self.manager
        )

        # Project created by employee
        self.emp_project = Project.objects.create(
            title='Employee Project',
            category='DevOps',
            deadline=date.today() + timedelta(days=10),
            status='Planned',
            created_by=self.employee_creator
        )

    def test_unauthorized_user_cannot_mark_project_done(self):
        """Standard employee cannot mark a project Done unless they created it."""
        self.client.login(username='emp', password='pwd')
        resp = self.client.post(f'/projects/{self.mgr_project.id}/submit-complete/')
        self.mgr_project.refresh_from_db()
        self.assertEqual(self.mgr_project.status, 'In Progress')

    def test_allowed_users_can_mark_project_done(self):
        """Manager, HR, Staff, or Project Creator can mark project Done."""
        # Employee creator marks their own project Done
        self.client.login(username='emp_creator', password='pwd')
        resp = self.client.post(f'/projects/{self.emp_project.id}/submit-complete/')
        self.emp_project.refresh_from_db()
        self.assertEqual(self.emp_project.status, 'Done')

        # Manager marks manager project Done
        self.client.login(username='mgr', password='pwd')
        resp = self.client.post(f'/projects/{self.mgr_project.id}/submit-complete/')
        self.mgr_project.refresh_from_db()
        self.assertEqual(self.mgr_project.status, 'Done')

    def test_unauthorized_user_cannot_upload_asset(self):
        """Standard employee cannot upload assets to a project they didn't create."""
        self.client.login(username='emp', password='pwd')
        f = SimpleUploadedFile("doc.pdf", b"sample content", content_type="application/pdf")
        resp = self.client.post(f'/projects/{self.mgr_project.id}/upload-asset/', {'assets': [f]})
        self.assertEqual(self.mgr_project.assets.count(), 0)

    def test_allowed_users_can_upload_asset(self):
        """Project creator and managers can upload assets."""
        self.client.login(username='mgr', password='pwd')
        f = SimpleUploadedFile("spec.pdf", b"sample content", content_type="application/pdf")
        resp = self.client.post(f'/projects/{self.mgr_project.id}/upload-asset/', {'assets': [f]})
        self.assertEqual(self.mgr_project.assets.count(), 1)

    def test_disallowed_file_type_rejected(self):
        """Disallowed extensions like .exe, .sh, and .svg are rejected."""
        self.client.login(username='mgr', password='pwd')
        f_exe = SimpleUploadedFile("malware.exe", b"MZ...", content_type="application/x-msdownload")
        f_svg = SimpleUploadedFile("vector.svg", b"<svg></svg>", content_type="image/svg+xml")
        
        resp = self.client.post(f'/projects/{self.mgr_project.id}/upload-asset/', {'assets': [f_exe]})
        self.assertEqual(self.mgr_project.assets.count(), 0)

        resp2 = self.client.post(f'/projects/{self.mgr_project.id}/upload-asset/', {'assets': [f_svg]})
        self.assertEqual(self.mgr_project.assets.count(), 0)

    def test_oversized_file_rejected(self):
        """Files larger than 10MB are rejected."""
        self.client.login(username='mgr', password='pwd')
        big_content = b'0' * (10 * 1024 * 1024 + 1024)
        big_file = SimpleUploadedFile("large_archive.zip", big_content, content_type="application/zip")
        resp = self.client.post(f'/projects/{self.mgr_project.id}/upload-asset/', {'assets': [big_file]})
        self.assertEqual(self.mgr_project.assets.count(), 0)

    def test_unauthorized_user_cannot_delete_asset(self):
        """User cannot delete assets uploaded by another user unless creator/manager/staff."""
        asset = ProjectAsset.objects.create(
            project=self.mgr_project,
            file=SimpleUploadedFile("doc.pdf", b"pdf content", content_type="application/pdf"),
            name="doc.pdf",
            uploaded_by=self.manager
        )
        self.client.login(username='emp', password='pwd')
        resp = self.client.post(f'/projects/asset/{asset.id}/delete/')
        self.assertTrue(ProjectAsset.objects.filter(id=asset.id).exists())

    def test_download_asset_protected_and_headers(self):
        """Download view requires login, has nosniff header, and safe disposition."""
        asset_img = ProjectAsset.objects.create(
            project=self.mgr_project,
            file=SimpleUploadedFile("chart.png", b"fake image", content_type="image/png"),
            name="chart.png",
            uploaded_by=self.manager
        )
        quote_name = 'report "Q1" final.pdf'
        asset_pdf = ProjectAsset.objects.create(
            project=self.mgr_project,
            file=SimpleUploadedFile("report.pdf", b"fake pdf", content_type="application/pdf"),
            name=quote_name,
            uploaded_by=self.manager
        )

        # Unauthenticated access redirects to login
        anon_client = Client()
        resp_anon = anon_client.get(f'/projects/asset/{asset_pdf.id}/download/')
        self.assertEqual(resp_anon.status_code, 302)

        # Authenticated access
        self.client.login(username='emp', password='pwd')
        resp_img = self.client.get(f'/projects/asset/{asset_img.id}/download/')
        self.assertEqual(resp_img.status_code, 200)
        self.assertEqual(resp_img.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertIn('inline', resp_img.headers.get('Content-Disposition', ''))

        resp_pdf = self.client.get(f'/projects/asset/{asset_pdf.id}/download/')
        self.assertEqual(resp_pdf.status_code, 200)
        self.assertEqual(resp_pdf.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertIn('attachment', resp_pdf.headers.get('Content-Disposition', ''))
        # Content-Disposition should safely escape quotes
        cd_header = resp_pdf.headers.get('Content-Disposition', '')
        self.assertNotIn('filename="report "Q1"', cd_header)

    def test_missing_file_shows_clear_message(self):
        """When an asset file is missing from storage, a clear message is shown instead of a server error."""
        asset = ProjectAsset.objects.create(
            project=self.mgr_project,
            file=SimpleUploadedFile("missing.pdf", b"initial content", content_type="application/pdf"),
            name="missing.pdf",
            uploaded_by=self.manager
        )
        if asset.file.storage.exists(asset.file.name):
            asset.file.storage.delete(asset.file.name)

        self.client.login(username='emp', password='pwd')
        resp = self.client.get(f'/projects/asset/{asset.id}/download/', follow=True)
        self.assertEqual(resp.status_code, 200)
        messages_list = list(resp.context['messages'])
        self.assertTrue(any('could not be found' in str(m) for m in messages_list))

    @override_settings(DEBUG=False)
    def test_download_asset_with_debug_false(self):
        """Project assets download correctly even when DEBUG is False in production."""
        asset = ProjectAsset.objects.create(
            project=self.mgr_project,
            file=SimpleUploadedFile("prod_guide.pdf", b"%PDF-1.4 prod document", content_type="application/pdf"),
            name="prod_guide.pdf",
            uploaded_by=self.manager
        )
        self.client.login(username='emp', password='pwd')
        resp = self.client.get(f'/projects/asset/{asset.id}/download/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertIn('attachment', resp.headers.get('Content-Disposition', ''))
