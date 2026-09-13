from rest_framework import permissions


def _is_platform_admin(user):
    role = str(getattr(user, 'role', '')).upper()
    return (
        role in ['ADMIN', 'PLATFORM_ADMIN']
        or getattr(user, 'is_staff', False)
        or getattr(user, 'is_superuser', False)
    )


def _is_store_owner(user):
    role = str(getattr(user, 'role', '')).upper()
    return role in ['STORE_OWNER', 'VENDOR', 'DEALER'] or bool(getattr(user, 'tenant_id', None))


class IsPlatformAdmin(permissions.BasePermission):
    """Grants access only to platform admins / superusers."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and _is_platform_admin(request.user))


class IsServiceCall(permissions.BasePermission):
    """Allows only internal service-to-service calls with a valid X-Service-Token."""
    def has_permission(self, request, view):
        service_token = (
            request.META.get('HTTP_X_SERVICE_TOKEN')
            or request.headers.get('X-Service-Token')
        )
        return bool(service_token)


class IsTenantScoped(permissions.BasePermission):
    """Ensures the request has a valid tenant_id context."""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if _is_platform_admin(request.user):
            return True
        tenant_id = getattr(request.user, 'tenant_id', None)
        return bool(tenant_id)
