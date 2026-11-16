from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User, AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from accounts.models import UserProfile, SystemMessage
from accounts.decorators import hr_required, manager_or_hr_required


@hr_required
def dummy_hr_view(request):
    return HttpResponse("hr_ok")


@manager_or_hr_required
def dummy_manager_or_hr_view(request):
    return HttpResponse("mgr_hr_ok")


class RoleDecoratorTests(TestCase):
    def setUp(self):
        self.rf = RequestFactory()

        self.superuser = User.objects.create_superuser(username='super', password='password123', email='super@example.com')
        
        self.hr_user = User.objects.create_user(username='hr_user', password='password123')
        UserProfile.objects.filter(user=self.hr_user).update(role='hr')
        self.hr_user = User.objects.get(pk=self.hr_user.pk)

        self.manager_user = User.objects.create_user(username='mgr_user', password='password123')
        UserProfile.objects.filter(user=self.manager_user).update(role='manager')
        self.manager_user = User.objects.get(pk=self.manager_user.pk)

        self.employee_user = User.objects.create_user(username='emp_user', password='password123')
        UserProfile.objects.filter(user=self.employee_user).update(role='employee')
        self.employee_user = User.objects.get(pk=self.employee_user.pk)

        self.client = Client()

    def test_hr_required_decorator(self):
        # Superuser allowed
        req = self.rf.get('/')
        req.user = self.superuser
        resp = dummy_hr_view(req)
        self.assertEqual(resp.content, b"hr_ok")

        # HR user allowed
        req.user = self.hr_user
        resp = dummy_hr_view(req)
        self.assertEqual(resp.content, b"hr_ok")

        # Manager user denied
        req.user = self.manager_user
        with self.assertRaises(PermissionDenied):
            dummy_hr_view(req)

        # Employee user denied
        req.user = self.employee_user
        with self.assertRaises(PermissionDenied):
            dummy_hr_view(req)

        # Anonymous user denied
        req.user = AnonymousUser()
        with self.assertRaises(PermissionDenied):
            dummy_hr_view(req)

    def test_manager_or_hr_required_decorator(self):
        # Superuser allowed
        req = self.rf.get('/')
        req.user = self.superuser
        resp = dummy_manager_or_hr_view(req)
        self.assertEqual(resp.content, b"mgr_hr_ok")

        # HR user allowed
        req.user = self.hr_user
        resp = dummy_manager_or_hr_view(req)
        self.assertEqual(resp.content, b"mgr_hr_ok")

        # Manager user allowed
        req.user = self.manager_user
        resp = dummy_manager_or_hr_view(req)
        self.assertEqual(resp.content, b"mgr_hr_ok")

        # Employee user denied
        req.user = self.employee_user
        with self.assertRaises(PermissionDenied):
            dummy_manager_or_hr_view(req)

        # Anonymous user denied
        req.user = AnonymousUser()
        with self.assertRaises(PermissionDenied):
            dummy_manager_or_hr_view(req)

    def test_view_protection_integration(self):
        # Employee blocked from manager/hr views
        self.client.login(username='emp_user', password='password123')
        resp_list = self.client.get('/dashboard/users/')
        self.assertEqual(resp_list.status_code, 403)

        resp_create = self.client.get('/dashboard/users/create/')
        self.assertEqual(resp_create.status_code, 403)

        # Manager allowed in user_list but blocked from user_create
        self.client.login(username='mgr_user', password='password123')
        resp_mgr_list = self.client.get('/dashboard/users/')
        self.assertEqual(resp_mgr_list.status_code, 200)

        resp_mgr_create = self.client.get('/dashboard/users/create/')
        self.assertEqual(resp_mgr_create.status_code, 403)


class AcknowledgeMessageTests(TestCase):
    def setUp(self):
        self.sender = User.objects.create_user(username='sender', password='password123')
        self.recipient = User.objects.create_user(username='recipient', password='password123')
        self.msg = SystemMessage.objects.create(
            sender=self.sender,
            recipient=self.recipient,
            content='Urgent notification'
        )
        self.client = Client()

    def test_acknowledge_requires_post(self):
        self.client.login(username='recipient', password='password123')
        
        # GET returns 405 Method Not Allowed instead of 500
        get_resp = self.client.get(f'/messages/{self.msg.id}/acknowledge/')
        self.assertEqual(get_resp.status_code, 405)
        self.msg.refresh_from_db()
        self.assertFalse(self.msg.is_read)

        # POST succeeds
        post_resp = self.client.post(f'/messages/{self.msg.id}/acknowledge/')
        self.assertEqual(post_resp.status_code, 200)
        self.msg.refresh_from_db()
        self.assertTrue(self.msg.is_read)
