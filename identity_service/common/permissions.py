from rest_framework import permissions


def _is_platform_admin(user):
    role = str(getattr(user, 'role', '')).upper()
    return (
        role in ['ADMIN', 'PLATFORM_ADMIN']
        or getattr(user, 'is_staff', False)
        or getattr(user, 'is_superuser', False)
    )


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
