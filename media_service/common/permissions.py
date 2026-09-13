from rest_framework import permissions

class IsPlatformAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        role = str(getattr(request.user, 'role', '')).upper()
        return role in ['ADMIN', 'PLATFORM_ADMIN'] or getattr(request.user, 'is_staff', False) or getattr(request.user, 'is_superuser', False)


class IsStoreOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        role = getattr(request.user, 'role', '').upper()
        tenant_id = getattr(request.user, 'tenant_id', None)
        return role in ['STORE_OWNER', 'VENDOR', 'DEALER'] or tenant_id is not None

class IsStoreOwnerOrPlatformAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        role = getattr(request.user, 'role', '').upper()
        tenant_id = getattr(request.user, 'tenant_id', None)
        is_admin = role == 'ADMIN' or getattr(request.user, 'is_staff', False) or getattr(request.user, 'is_superuser', False)
        is_store_owner = role in ['STORE_OWNER', 'VENDOR', 'DEALER'] or tenant_id is not None
        return is_admin or is_store_owner
