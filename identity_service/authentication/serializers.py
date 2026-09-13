from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User, Tenant, Subscription, UserProfile, ActivityLog, UserAddress, Notification, TenantMembership, DEFAULT_ROLE_PERMISSIONS

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['user_id'] = str(user.id)
        token['email'] = user.email
        token['username'] = user.username
        
        is_admin = getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False) or getattr(user, 'role', '') == 'PLATFORM_ADMIN'
        user_role = 'PLATFORM_ADMIN' if is_admin else getattr(user, 'role', 'STORE_OWNER')

        token['role'] = user_role
        token['is_staff'] = user.is_staff
        token['is_superuser'] = user.is_superuser
        token['is_platform_admin'] = is_admin

        # Fetch tenant memberships
        memberships = TenantMembership.objects.filter(user=user, is_active=True).select_related('tenant')
        membership_list = []
        for m in memberships:
            membership_list.append({
                'tenant_id': str(m.tenant.id),
                'tenant_name': m.tenant.name,
                'role': m.role,
                'permissions': m.get_effective_permissions()
            })
        token['memberships'] = membership_list

        active_membership = memberships.first()
        owned_tenants = list(Tenant.objects.filter(owner=user))
        owned_tenant_ids = [str(t.id) for t in owned_tenants]
        token['owned_tenant_ids'] = owned_tenant_ids

        owned_tenant = next((t for t in owned_tenants if t.status == 'ACTIVE'), owned_tenants[0] if owned_tenants else None)

        if owned_tenant:
            token['tenant_id'] = str(owned_tenant.id)
            token['subscription_tier'] = owned_tenant.subscription_tier
            token['permissions'] = DEFAULT_ROLE_PERMISSIONS.get('SHOP_OWNER', [])
        elif active_membership:
            token['tenant_id'] = str(active_membership.tenant.id)
            token['subscription_tier'] = active_membership.tenant.subscription_tier
            token['permissions'] = active_membership.get_effective_permissions()
        else:
            token['tenant_id'] = None
            token['subscription_tier'] = 'STARTER'
            token['permissions'] = [] if not is_admin else ['*']

        return token



class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ['id', 'name', 'domain', 'owner', 'subscription_tier', 'status', 'has_catalog_access', 'has_inventory_access', 'has_finance_access', 'has_payment_access', 'created_at']
        read_only_fields = ['owner']

class ConfigureSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ['subscription_tier', 'status', 'has_catalog_access', 'has_inventory_access', 'has_finance_access', 'has_payment_access']

class UserProfileSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='user.id', read_only=True)
    user_id = serializers.CharField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    role = serializers.CharField(source='user.role', read_only=True)
    first_name = serializers.CharField(source='user.first_name', required=False, allow_blank=True)
    last_name = serializers.CharField(source='user.last_name', required=False, allow_blank=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'user_id', 'username', 'email', 'role', 'first_name', 'last_name', 'phone_number', 'address', 'bio', 'avatar_url', 'created_at', 'updated_at']

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        first_name = user_data.get('first_name')
        last_name = user_data.get('last_name')

        if first_name is not None or last_name is not None:
            user = instance.user
            if first_name is not None:
                user.first_name = first_name
            if last_name is not None:
                user.last_name = last_name
            user.save(update_fields=['first_name', 'last_name'])

        return super().update(instance, validated_data)

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    role = serializers.CharField(required=False, default='STORE_OWNER')

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'role']

    def create(self, validated_data):
        role = validated_data.get('role', 'STORE_OWNER')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role=role
        )
        UserProfile.objects.create(user=user)
        ActivityLog.objects.create(
            actor_id=user.id,
            actor_email=user.email,
            actor_role=role,
            action="user.registered",
            resource_type="USER",
            resource_id=str(user.id),
            status="SUCCESS",
            details={"email": user.email, "username": user.username, "role": role}
        )
        return user


class ActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityLog
        fields = [
            'id', 'tenant_id', 'actor_id', 'actor_email', 'actor_role',
            'action', 'resource_type', 'resource_id', 'status',
            'ip_address', 'user_agent', 'details', 'changes', 'timestamp'
        ]

class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = [
            'id', 'user', 'title', 'full_name', 'phone_number', 'address_type',
            'address_line_1', 'address_line_2', 'city', 'state', 'postal_code',
            'country', 'is_default', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user']

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'user', 'title', 'message', 'notification_type', 'is_read', 'metadata', 'created_at']
        read_only_fields = ['user']
