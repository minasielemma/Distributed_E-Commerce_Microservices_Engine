import uuid
import io
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status

from media.models import MediaFile


def make_user(username='user1', role='USER', tenant_id=None):
    from django.contrib.auth.models import User
    user = User.objects.create_user(username=username, password='pass123')
    user.role = role
    user.tenant_id = tenant_id or uuid.uuid4()
    return user


class MediaServiceTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.tenant_a = uuid.uuid4()
        self.tenant_b = uuid.uuid4()
        self.user1 = make_user('owner_user', role='STORE_OWNER', tenant_id=self.tenant_a)
        self.user2 = make_user('other_user', role='USER', tenant_id=self.tenant_a)
        self.user3 = make_user('third_user', role='USER', tenant_id=self.tenant_b)
        self.admin = make_user('admin_user', role='ADMIN')

    def test_upload_public_image_success(self):
        self.client.force_authenticate(user=self.user1)
        image_data = SimpleUploadedFile("product_img.jpg", b"fake_image_binary_content", content_type="image/jpeg")
        response = self.client.post('/api/media/upload/', {'file': image_data, 'visibility': 'PUBLIC'}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('file_id', response.data)
        self.assertEqual(response.data['visibility'], 'PUBLIC')
        file_id = response.data['file_id']
        self.assertTrue(MediaFile.objects.filter(id=file_id).exists())

    def test_upload_unsupported_file_type_fails(self):
        self.client.force_authenticate(user=self.user1)
        script_file = SimpleUploadedFile("malicious.exe", b"executable_binary", content_type="application/octet-stream")
        response = self.client.post('/api/media/upload/', {'file': script_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Unsupported file extension', str(response.data))

    def test_public_file_accessible_unauthenticated(self):
        self.client.force_authenticate(user=self.user1)
        image_data = SimpleUploadedFile("public.jpg", b"public_binary_data", content_type="image/jpeg")
        upload_resp = self.client.post('/api/media/upload/', {'file': image_data, 'visibility': 'PUBLIC'}, format='multipart')
        file_id = upload_resp.data['file_id']

        # Unauthenticated client gets detail and download
        self.client.logout()
        anon_client = APIClient()
        detail_resp = anon_client.get(f'/api/media/files/{file_id}/')
        self.assertEqual(detail_resp.status_code, status.HTTP_200_OK)

        download_resp = anon_client.get(f'/api/media/files/{file_id}/download/')
        self.assertEqual(download_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(b"".join(download_resp.streaming_content), b"public_binary_data")

    def test_private_file_access_restricted(self):
        self.client.force_authenticate(user=self.user1)
        image_data = SimpleUploadedFile("private.png", b"private_content", content_type="image/png")
        upload_resp = self.client.post('/api/media/upload/', {'file': image_data, 'visibility': 'PRIVATE'}, format='multipart')
        file_id = upload_resp.data['file_id']

        # Owner gets access & download
        owner_resp = self.client.get(f'/api/media/files/{file_id}/')
        self.assertEqual(owner_resp.status_code, status.HTTP_200_OK)
        owner_dl = self.client.get(f'/api/media/files/{file_id}/download/')
        self.assertEqual(owner_dl.status_code, status.HTTP_200_OK)

        # Unauthenticated user denied (401)
        anon_client = APIClient()
        unauth_resp = anon_client.get(f'/api/media/files/{file_id}/')
        self.assertEqual(unauth_resp.status_code, status.HTTP_401_UNAUTHORIZED)

        # Other user denied access (403)
        self.client.force_authenticate(user=self.user2)
        other_resp = self.client.get(f'/api/media/files/{file_id}/')
        self.assertEqual(other_resp.status_code, status.HTTP_403_FORBIDDEN)

        # Admin gets access
        self.client.force_authenticate(user=self.admin)
        admin_resp = self.client.get(f'/api/media/files/{file_id}/')
        self.assertEqual(admin_resp.status_code, status.HTTP_200_OK)

    def test_shared_file_access_by_user_and_tenant(self):
        self.client.force_authenticate(user=self.user1)
        image_data = SimpleUploadedFile("shared.png", b"shared_content", content_type="image/png")
        upload_resp = self.client.post('/api/media/upload/', {
            'file': image_data,
            'visibility': 'SHARED',
            'shared_with_users': [str(self.user2.id)],
            'shared_with_tenants': [str(self.tenant_b)]
        }, format='multipart')
        self.assertEqual(upload_resp.status_code, status.HTTP_201_CREATED, upload_resp.data)
        file_id = upload_resp.data['file_id']

        # Shared user2 gets access
        self.client.force_authenticate(user=self.user2)
        shared_resp = self.client.get(f'/api/media/files/{file_id}/')
        self.assertEqual(shared_resp.status_code, status.HTTP_200_OK)

        # User3 (tenant_b) gets access via tenant sharing
        self.client.force_authenticate(user=self.user3)
        tenant_resp = self.client.get(f'/api/media/files/{file_id}/')
        self.assertEqual(tenant_resp.status_code, status.HTTP_200_OK)

    def test_share_media_view_update_permissions(self):
        self.client.force_authenticate(user=self.user1)
        image_data = SimpleUploadedFile("doc.pdf", b"pdf_content", content_type="application/pdf")
        upload_resp = self.client.post('/api/media/upload/', {'file': image_data, 'visibility': 'PRIVATE'}, format='multipart')
        file_id = upload_resp.data['file_id']

        # User2 tries to access -> 403
        self.client.force_authenticate(user=self.user2)
        self.assertEqual(self.client.get(f'/api/media/files/{file_id}/').status_code, status.HTTP_403_FORBIDDEN)

        # Owner shares file with User2
        self.client.force_authenticate(user=self.user1)
        share_resp = self.client.post(f'/api/media/files/{file_id}/share/', {
            'visibility': 'SHARED',
            'shared_with_users': [str(self.user2.id)]
        }, format='json')
        self.assertEqual(share_resp.status_code, status.HTTP_200_OK, share_resp.data)

        # User2 now gets access
        self.client.force_authenticate(user=self.user2)
        self.assertEqual(self.client.get(f'/api/media/files/{file_id}/').status_code, status.HTTP_200_OK)

    def test_delete_file_by_non_owner_fails(self):
        self.client.force_authenticate(user=self.user1)
        image_data = SimpleUploadedFile("doc.pdf", b"pdf_content", content_type="application/pdf")
        upload_resp = self.client.post('/api/media/upload/', {'file': image_data}, format='multipart')
        file_id = upload_resp.data['file_id']

        self.client.force_authenticate(user=self.user2)
        del_resp = self.client.delete(f'/api/media/files/{file_id}/')
        self.assertEqual(del_resp.status_code, status.HTTP_403_FORBIDDEN)
