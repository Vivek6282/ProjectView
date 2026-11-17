import io
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.models import UserProfile
from chat.models import ChatRoom, ChatMessage


class MessageForwardingSecurityTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(username='alice', password='password123')
        UserProfile.objects.get_or_create(user=self.alice, defaults={'role': 'manager'})

        self.bob = User.objects.create_user(username='bob', password='password123')
        UserProfile.objects.get_or_create(user=self.bob, defaults={'role': 'employee'})

        self.secret_room = ChatRoom.objects.create(
            name='Secret HR Bridge',
            room_type='GROUP',
            created_by=self.alice
        )
        self.secret_room.members.add(self.alice)

        self.public_room = ChatRoom.objects.create(
            name='General Discussion',
            room_type='GROUP',
            created_by=self.bob
        )
        self.public_room.members.add(self.alice, self.bob)

        self.secret_msg = ChatMessage.objects.create(
            room=self.secret_room,
            sender=self.alice,
            content='Top secret message'
        )

        self.client = Client()

    def test_non_member_cannot_forward_message(self):
        """Bob is not a member of secret_room, so he cannot forward secret_msg."""
        self.client.login(username='bob', password='password123')
        response = self.client.post(
            f'/chat/api/messages/{self.secret_msg.id}/forward/',
            {'room_id': self.public_room.id}
        )
        self.assertIn(response.status_code, [403, 404])
        self.assertEqual(self.public_room.messages.count(), 0)

    def test_member_can_forward_message(self):
        """Alice is a member of secret_room and public_room, so she can forward it."""
        self.client.login(username='alice', password='password123')
        response = self.client.post(
            f'/chat/api/messages/{self.secret_msg.id}/forward/',
            {'room_id': self.public_room.id}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.public_room.messages.count(), 1)


class RoomDeletionPermissionTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(username='staff1', password='password123', is_staff=True)
        UserProfile.objects.get_or_create(user=self.staff_user, defaults={'role': 'manager'})

        self.creator_emp = User.objects.create_user(username='creator_emp', password='password123')
        UserProfile.objects.get_or_create(user=self.creator_emp, defaults={'role': 'employee'})

        self.other_emp = User.objects.create_user(username='other_emp', password='password123')
        UserProfile.objects.get_or_create(user=self.other_emp, defaults={'role': 'employee'})

        self.client = Client()

    def test_non_member_staff_cannot_delete_group_room(self):
        room = ChatRoom.objects.create(name='Team Group', room_type='GROUP', created_by=self.creator_emp)
        room.members.add(self.creator_emp, self.other_emp)
        # staff_user is NOT a member

        self.client.login(username='staff1', password='password123')
        response = self.client.post(f'/chat/api/{room.id}/delete/')
        self.assertEqual(response.status_code, 403)
        self.assertTrue(ChatRoom.objects.filter(id=room.id).exists())

    def test_member_staff_can_delete_group_room(self):
        room = ChatRoom.objects.create(name='Team Group', room_type='GROUP', created_by=self.creator_emp)
        room.members.add(self.creator_emp, self.staff_user)

        self.client.login(username='staff1', password='password123')
        response = self.client.post(f'/chat/api/{room.id}/delete/')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ChatRoom.objects.filter(id=room.id).exists())

    def test_creator_can_delete_group_room(self):
        room = ChatRoom.objects.create(name='My Group', room_type='GROUP', created_by=self.creator_emp)
        room.members.add(self.creator_emp, self.other_emp)

        self.client.login(username='creator_emp', password='password123')
        response = self.client.post(f'/chat/api/{room.id}/delete/')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ChatRoom.objects.filter(id=room.id).exists())

    def test_plain_employee_member_cannot_delete_group_room(self):
        room = ChatRoom.objects.create(name='My Group', room_type='GROUP', created_by=self.creator_emp)
        room.members.add(self.creator_emp, self.other_emp)

        self.client.login(username='other_emp', password='password123')
        response = self.client.post(f'/chat/api/{room.id}/delete/')
        self.assertEqual(response.status_code, 403)
        self.assertTrue(ChatRoom.objects.filter(id=room.id).exists())

    def test_cannot_delete_general_system_room(self):
        general_room, _ = ChatRoom.objects.get_or_create(
            system_name='general',
            defaults={'name': 'General', 'room_type': 'PUBLIC', 'is_system': True, 'created_by': self.staff_user}
        )
        general_room.members.add(self.staff_user)

        self.client.login(username='staff1', password='password123')
        response = self.client.post(f'/chat/api/{general_room.id}/delete/')
        self.assertEqual(response.status_code, 400)
        self.assertTrue(ChatRoom.objects.filter(id=general_room.id).exists())

    def test_cannot_delete_hr_bridge_system_room(self):
        bridge_room, _ = ChatRoom.objects.get_or_create(
            system_name='hr_bridge',
            defaults={'name': 'HR-Management Bridge', 'room_type': 'GROUP', 'is_system': True, 'created_by': self.staff_user}
        )
        bridge_room.members.add(self.staff_user)

        self.client.login(username='staff1', password='password123')
        response = self.client.post(f'/chat/api/{bridge_room.id}/delete/')
        self.assertEqual(response.status_code, 400)
        self.assertTrue(ChatRoom.objects.filter(id=bridge_room.id).exists())

    def test_cannot_delete_direct_room(self):
        direct_room = ChatRoom.objects.create(
            name='Direct Chat',
            room_type='DIRECT',
            created_by=self.staff_user
        )
        direct_room.members.add(self.staff_user, self.other_emp)

        self.client.login(username='staff1', password='password123')
        response = self.client.post(f'/chat/api/{direct_room.id}/delete/')
        self.assertEqual(response.status_code, 400)
        self.assertTrue(ChatRoom.objects.filter(id=direct_room.id).exists())


class ChatMessageMembershipTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(username='alice', password='password123')
        UserProfile.objects.get_or_create(user=self.alice, defaults={'role': 'employee'})

        self.bob = User.objects.create_user(username='bob', password='password123')
        UserProfile.objects.get_or_create(user=self.bob, defaults={'role': 'employee'})

        self.room = ChatRoom.objects.create(name='Alice Room', room_type='GROUP', created_by=self.alice)
        self.room.members.add(self.alice)

        self.msg = ChatMessage.objects.create(room=self.room, sender=self.alice, content='Hello')
        self.client = Client()

    def test_non_member_cannot_list_messages(self):
        self.client.login(username='bob', password='password123')
        resp1 = self.client.get(f'/chat/api/{self.room.id}/messages/')
        self.assertEqual(resp1.status_code, 404)

        resp2 = self.client.get(f'/chat/api/{self.room.id}/messages/?page=1')
        self.assertEqual(resp2.status_code, 404)

    def test_non_member_cannot_send_message(self):
        self.client.login(username='bob', password='password123')
        resp = self.client.post(f'/chat/api/{self.room.id}/send/', {'content': 'Intrusion'})
        self.assertEqual(resp.status_code, 404)

    def test_non_member_cannot_edit_message(self):
        self.client.login(username='bob', password='password123')
        resp = self.client.post(f'/chat/api/messages/{self.msg.id}/edit/', {'content': 'Edited content'})
        self.assertEqual(resp.status_code, 404)

    def test_non_member_cannot_delete_message(self):
        self.client.login(username='bob', password='password123')
        resp = self.client.post(f'/chat/api/messages/{self.msg.id}/delete/')
        self.assertEqual(resp.status_code, 404)

    def test_member_can_list_and_send_and_edit_and_delete(self):
        self.client.login(username='alice', password='password123')
        
        # List
        resp = self.client.get(f'/chat/api/{self.room.id}/messages/')
        self.assertEqual(resp.status_code, 200)

        # Send
        resp = self.client.post(f'/chat/api/{self.room.id}/send/', {'content': 'Second message'})
        self.assertEqual(resp.status_code, 200)
        new_id = resp.json()['message']['id']

        # Edit
        resp = self.client.post(f'/chat/api/messages/{new_id}/edit/', {'content': 'Second message edited'})
        self.assertEqual(resp.status_code, 200)

        # Delete
        resp = self.client.post(f'/chat/api/messages/{new_id}/delete/')
        self.assertEqual(resp.status_code, 200)


class ChatAttachmentTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(username='alice', password='password123')
        UserProfile.objects.get_or_create(user=self.alice, defaults={'role': 'employee'})

        self.bob = User.objects.create_user(username='bob', password='password123')
        UserProfile.objects.get_or_create(user=self.bob, defaults={'role': 'employee'})

        self.room = ChatRoom.objects.create(name='Attachment Room', room_type='GROUP', created_by=self.alice)
        self.room.members.add(self.alice)

        self.client = Client()

    def test_disallowed_extension_upload_rejected(self):
        self.client.login(username='alice', password='password123')
        bad_file = SimpleUploadedFile("malicious.svg", b"<svg><script>alert(1)</script></svg>", content_type="image/svg+xml")
        resp = self.client.post(f'/chat/api/{self.room.id}/send/', {'content': 'Check this', 'attachment': bad_file})
        self.assertEqual(resp.status_code, 400)
        self.assertIn('not allowed', resp.json().get('error', '').lower())

    def test_oversized_upload_rejected(self):
        self.client.login(username='alice', password='password123')
        # 11 MB file
        big_data = b"0" * (11 * 1024 * 1024)
        big_file = SimpleUploadedFile("big.png", big_data, content_type="image/png")
        resp = self.client.post(f'/chat/api/{self.room.id}/send/', {'content': 'Too big', 'attachment': big_file})
        self.assertEqual(resp.status_code, 400)
        self.assertIn('10 mb', resp.json().get('error', '').lower())

    def test_valid_attachment_upload_and_download_permissions(self):
        self.client.login(username='alice', password='password123')
        valid_file = SimpleUploadedFile("doc.pdf", b"%PDF-1.4 sample content", content_type="application/pdf")
        resp = self.client.post(f'/chat/api/{self.room.id}/send/', {'content': 'My Doc', 'attachment': valid_file})
        self.assertEqual(resp.status_code, 200)
        msg_id = resp.json()['message']['id']

        # Alice (member) can download attachment
        dl_resp = self.client.get(f'/chat/api/messages/{msg_id}/attachment/')
        self.assertEqual(dl_resp.status_code, 200)
        self.assertEqual(dl_resp.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertIn('attachment', dl_resp.headers.get('Content-Disposition', ''))

        # Bob (non-member) cannot download attachment
        self.client.login(username='bob', password='password123')
        dl_resp_bob = self.client.get(f'/chat/api/messages/{msg_id}/attachment/')
        self.assertEqual(dl_resp_bob.status_code, 403)

    def test_chat_attachment_filename_with_quotes(self):
        self.client.login(username='alice', password='password123')
        quoted_filename = 'quarterly "report".pdf'
        file_obj = SimpleUploadedFile(quoted_filename, b"pdf binary content", content_type="application/pdf")
        resp = self.client.post(f'/chat/api/{self.room.id}/send/', {'content': 'Here is file', 'attachment': file_obj})
        self.assertEqual(resp.status_code, 200)
        msg_id = resp.json()['message']['id']

        dl_resp = self.client.get(f'/chat/api/messages/{msg_id}/attachment/')
        self.assertEqual(dl_resp.status_code, 200)
        cd = dl_resp.headers.get('Content-Disposition', '')
        # Unescaped quote like filename="quarterly "report".pdf" is broken HTTP header syntax
        self.assertNotIn('filename="quarterly "report"', cd)


class ChatPaginationTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(username='alice', password='password123')
        UserProfile.objects.get_or_create(user=self.alice, defaults={'role': 'employee'})

        self.room = ChatRoom.objects.create(name='Paging Room', room_type='GROUP', created_by=self.alice)
        self.room.members.add(self.alice)
        for i in range(5):
            ChatMessage.objects.create(room=self.room, sender=self.alice, content=f'Msg {i}')

        self.client = Client()
        self.client.login(username='alice', password='password123')

    def test_invalid_page_falls_back_gracefully(self):
        # String page
        resp_str = self.client.get(f'/chat/api/{self.room.id}/messages/?page=abc')
        self.assertEqual(resp_str.status_code, 200)
        self.assertEqual(len(resp_str.json()['messages']), 5)

        # Negative page
        resp_neg = self.client.get(f'/chat/api/{self.room.id}/messages/?page=-3')
        self.assertEqual(resp_neg.status_code, 200)
        self.assertEqual(len(resp_neg.json()['messages']), 5)

        # Zero page
        resp_zero = self.client.get(f'/chat/api/{self.room.id}/messages/?page=0')
        self.assertEqual(resp_zero.status_code, 200)
        self.assertEqual(len(resp_zero.json()['messages']), 5)
