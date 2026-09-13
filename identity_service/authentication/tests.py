import uuid
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from .models import User, Tenant, Subscription, UserProfile, ActivityLog, UserAddress, Notification


class RegisterViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('auth_register')

    def test_register_success(self):
        data = {'username': 'testuser', 'email': 'test@example.com', 'password': 'pass123'}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='testuser').exists())

    def test_register_creates_profile_and_activity_log(self):
        data = {'username': 'newuser', 'email': 'new@example.com', 'password': 'pass123'}
        self.client.post(self.url, data)
        user = User.objects.get(username='newuser')
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
        self.assertTrue(ActivityLog.objects.filter(actor_id=user.id, action='user.registered').exists())

    def test_register_duplicate_email_fails(self):
        User.objects.create_user(username='existing', email='dup@example.com', password='pass123')
        data = {'username': 'other', 'email': 'dup@example.com', 'password': 'pass123'}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_fields_fails(self):
        response = self.client.post(self.url, {'username': 'only'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_short_password_fails(self):
        data = {'username': 'shortpass', 'email': 'short@example.com', 'password': '123'}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_token_contains_role_claims(self):
        user = User.objects.create_user(username='adminusr', email='adminusr@example.com', password='pass123', is_staff=True, role='PLATFORM_ADMIN')
        from .serializers import CustomTokenObtainPairSerializer
        token = CustomTokenObtainPairSerializer.get_token(user)
        self.assertEqual(token['role'], 'PLATFORM_ADMIN')
        self.assertTrue(token['is_platform_admin'])



class TenantViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='owner', email='owner@example.com', password='pass123')
        self.client.force_authenticate(user=self.user)

    def test_create_tenant_success(self):
        url = reverse('tenant_create')
        data = {'name': 'My Shop', 'domain': 'myshop.com', 'subscription_tier': 'STARTER'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Tenant.objects.filter(domain='myshop.com').exists())

    def test_create_tenant_creates_subscription_and_activity_log(self):
        url = reverse('tenant_create')
        data = {'name': 'Shop2', 'domain': 'shop2.com', 'subscription_tier': 'GROWTH'}
        self.client.post(url, data)
        tenant = Tenant.objects.get(domain='shop2.com')
        self.assertTrue(Subscription.objects.filter(tenant=tenant).exists())
        self.assertTrue(ActivityLog.objects.filter(action='tenant.created').exists())

    def test_create_tenant_unauthenticated_fails(self):
        self.client.force_authenticate(user=None)
        url = reverse('tenant_create')
        response = self.client.post(url, {'name': 'X', 'domain': 'x.com'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_tenants_returns_only_own(self):
        other_user = User.objects.create_user(username='other', email='other@example.com', password='pass123')
        Tenant.objects.create(name='OtherShop', domain='other.com', owner=other_user)
        Tenant.objects.create(name='MyShop', domain='mine.com', owner=self.user)
        url = reverse('tenant_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['domain'], 'mine.com')

    def test_configure_subscription(self):
        tenant = Tenant.objects.create(name='Shop', domain='shop.com', owner=self.user)
        url = reverse('admin_configure_subscription', kwargs={'pk': tenant.pk})
        data = {'subscription_tier': 'ENTERPRISE', 'status': 'ACTIVE', 'has_catalog_access': True,
                'has_inventory_access': False, 'has_finance_access': True, 'has_payment_access': True}
        # Regular user receives 403 Forbidden
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Platform admin receives 200 OK
        self.user.role = 'PLATFORM_ADMIN'
        self.user.save()
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tenant.refresh_from_db()
        self.assertEqual(tenant.subscription_tier, 'ENTERPRISE')
        self.assertFalse(tenant.has_inventory_access)


class UserProfileViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='profuser', email='prof@example.com', password='pass123')
        self.client.force_authenticate(user=self.user)
        self.url = reverse('user_profile')

    def test_get_profile_creates_if_not_exists(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(UserProfile.objects.filter(user=self.user).exists())

    def test_update_profile(self):
        UserProfile.objects.create(user=self.user)
        response = self.client.patch(self.url, {'phone_number': '+1234567890', 'bio': 'Hello'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.phone_number, '+1234567890')


class UserAddressAndNotificationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='addruser', email='addr@example.com', password='pass123')
        self.client.force_authenticate(user=self.user)

    def test_create_address(self):
        data = {
            'title': 'Home',
            'full_name': 'John Doe',
            'phone_number': '+11223344',
            'address_type': 'SHIPPING',
            'address_line_1': '123 Main St',
            'city': 'New York',
            'postal_code': '10001',
            'country': 'USA',
            'is_default': True
        }
        response = self.client.post('/api/auth/addresses/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserAddress.objects.filter(user=self.user).count(), 1)

    def test_mark_notification_as_read(self):
        notif = Notification.objects.create(
            user=self.user,
            title='Order Shipped',
            message='Your order #123 has been shipped!',
            notification_type='ORDER'
        )
        response = self.client.post(f'/api/auth/notifications/{notif.id}/read/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)

    def test_customer_address_ownership_isolation(self):
        other_user = User.objects.create_user(username='otheruser', email='otherusr@example.com', password='pass123')
        other_addr = UserAddress.objects.create(
            user=other_user,
            title='Office',
            full_name='Jane Doe',
            phone_number='+998877',
            address_line_1='456 Broad St',
            city='Boston',
            postal_code='02108',
            country='USA'
        )
        response = self.client.get('/api/auth/addresses/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertNotIn(str(other_addr.id), [str(item['id']) for item in results])


class MultiTenantRBACSecurityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(username='shopowner', email='owner@shopa.com', password='pass123', role='STORE_OWNER')
        self.tenant = Tenant.objects.create(name='Shop A', domain='shopa.com', owner=self.owner)
        self.staff_user = User.objects.create_user(username='productmgr', email='pm@shopa.com', password='pass123', role='CUSTOMER')
        from .models import TenantMembership
        self.membership = TenantMembership.objects.create(
            user=self.staff_user,
            tenant=self.tenant,
            role='PRODUCT_MANAGER'
        )

    def test_tenant_membership_effective_permissions(self):
        perms = self.membership.get_effective_permissions()
        self.assertIn('products.read', perms)
        self.assertIn('products.create', perms)
        self.assertNotIn('orders.refund', perms)
        self.assertNotIn('finance.manage', perms)

    def test_token_contains_tenant_membership_claims(self):
        from .serializers import CustomTokenObtainPairSerializer
        token = CustomTokenObtainPairSerializer.get_token(self.staff_user)
        self.assertEqual(token['tenant_id'], str(self.tenant.id))
        self.assertEqual(len(token['memberships']), 1)
        self.assertEqual(token['memberships'][0]['role'], 'PRODUCT_MANAGER')
        self.assertIn('products.create', token['permissions'])

    def test_activity_log_cross_tenant_isolation(self):
        # Create activity log for Shop A and Shop B
        other_user = User.objects.create_user(username='shopbowner', email='owner@shopb.com', password='pass123')
        other_tenant = Tenant.objects.create(name='Shop B', domain='shopb.com', owner=other_user)
        log_a = ActivityLog.objects.create(tenant_id=str(self.tenant.id), actor_id=self.owner.id, action='product.created')
        log_b = ActivityLog.objects.create(tenant_id=str(other_tenant.id), actor_id=other_user.id, action='product.created')

        self.client.force_authenticate(user=self.owner)
        response = self.client.get('/api/auth/activity/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        log_ids = [str(item['id']) for item in results]
        self.assertIn(str(log_a.id), log_ids)
        self.assertNotIn(str(log_b.id), log_ids)

