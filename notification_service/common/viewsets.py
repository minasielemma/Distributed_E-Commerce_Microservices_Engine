from rest_framework import viewsets, mixins, permissions
from rest_framework.response import Response

class BaseModelViewSet(viewsets.GenericViewSet):
    owner_field = "user"

    def get_queryset(self):
        assert self.queryset is not None, (
            "'%s' should either include a `queryset` attribute, "
            "or override the `get_queryset()` method." % self.__class__.__name__
        )

        queryset = self.queryset
        user = self.request.user
        if not user or user.is_anonymous:
            return queryset.none()
        
        if getattr(user, 'is_platform_admin', False) or getattr(user, 'is_superuser', False):
            return queryset.all()

        if hasattr(queryset.model, 'user_id'):
            return queryset.filter(user_id=user.id)
        elif hasattr(queryset.model, 'user'):
            return queryset.filter(user=user)
        return queryset.none()
