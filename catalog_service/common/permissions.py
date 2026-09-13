from rest_framework import permissions

def _is_platform_admin(user):
    if not user or not user.is_authenticated:
        return False
    if getattr(user, 'is_platform_admin', False) is True:
        return True
    role = str(getattr(user, 'role', '')).upper()
    # Explicit platform roles only
    if role in ['PLATFORM_ADMIN', 'SUPERADMIN', 'PLATFORM_SUPER_ADMIN', 'PLATFORM_SUPPORT', 'PLATFORM_FINANCE', 'PLATFORM_OPERATIONS']:
        return True
    if getattr(user, 'is_superuser', False):
        return True
    return False

def _is_store_owner_or_staff(user):
    if not user or not user.is_authenticated:
        return False
    role = str(getattr(user, 'role', '')).upper()
    tenant_id = getattr(user, 'tenant_id', None)
    return role in ['STORE_OWNER', 'SHOP_OWNER', 'SHOP_ADMIN', 'PRODUCT_MANAGER', 'ORDER_MANAGER', 'INVENTORY_MANAGER', 'CUSTOMER_SUPPORT', 'FINANCE_ACCOUNTING', 'SHOP_STAFF_LIMITED', 'VENDOR', 'DEALER', 'TENANT_ADMIN', 'OWNER'] or bool(tenant_id)

def get_user_permissions(user):
    if not user or not user.is_authenticated:
        return []
    if _is_platform_admin(user):
        return ['*']
    return getattr(user, 'permissions', []) or []

def has_resource_permission(user, permission_code):
    if not user or not user.is_authenticated:
        return False
    if _is_platform_admin(user):
        return True
    user_perms = get_user_permissions(user)
    if '*' in user_perms or permission_code in user_perms:
        return True
    # Fallback for store owners
    role = str(getattr(user, 'role', '')).upper()
    if role in ['STORE_OWNER', 'SHOP_OWNER', 'OWNER'] and getattr(user, 'tenant_id', None):
        return True
    return False

class HasResourcePermission(permissions.BasePermission):
    """
    DRF permission class that checks for a specific resource.action permission code.
    Usage: permission_classes = [HasResourcePermission('products.update')]
    """
    def __init__(self, permission_code=None):
        self.permission_code = permission_code

    def __call__(self):
        return self

    def has_permission(self, request, view):
        perm = self.permission_code or getattr(view, 'required_permission', None)
        if not perm:
            return request.user and request.user.is_authenticated
        return has_resource_permission(request.user, perm)

class IsPlatformAdmin(permissions.BasePermission):
    """Grants access only to platform admins."""
    def has_permission(self, request, view):
        return _is_platform_admin(request.user)

class IsStoreOwner(permissions.BasePermission):
    """Grants access only to store owners / staff with tenant scope."""
    def has_permission(self, request, view):
        return _is_store_owner_or_staff(request.user)

class IsStoreOwnerOrPlatformAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        return _is_platform_admin(request.user) or _is_store_owner_or_staff(request.user)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        if _is_platform_admin(request.user):
            return True
        user_tenant = str(getattr(request.user, 'tenant_id', '') or '')
        obj_tenant = str(getattr(obj, 'tenant_id', '') or '')
        if not obj_tenant:
            product = getattr(obj, 'product', None)
            if product:
                obj_tenant = str(getattr(product, 'tenant_id', '') or '')
        return bool(user_tenant and obj_tenant and user_tenant == obj_tenant)

class IsTenantMember(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if _is_platform_admin(request.user):
            return True
        user_tenant = str(getattr(request.user, 'tenant_id', '') or '')
        obj_tenant = str(getattr(obj, 'tenant_id', '') or '')
        if not obj_tenant:
            product = getattr(obj, 'product', None)
            if product:
                obj_tenant = str(getattr(product, 'tenant_id', '') or '')
        return bool(user_tenant and obj_tenant and user_tenant == obj_tenant)

class IsCustomerOwner(permissions.BasePermission):
    """Enforces that the resource customer_id or user_id matches request.user.id."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if _is_platform_admin(request.user):
            return True
        user_id = str(getattr(request.user, 'id', ''))
        obj_user = str(getattr(obj, 'customer_id', '') or getattr(obj, 'user_id', '') or getattr(obj, 'user', ''))
        return bool(user_id and obj_user and user_id == obj_user)
