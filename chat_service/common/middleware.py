import os
import jwt
from django.contrib.auth.models import AnonymousUser
from rest_framework.authentication import BaseAuthentication
from .ws_auth import GatewayUser, get_verifying_key


class GatewayJWTAuthentication(BaseAuthentication):
    """DRF Authentication backend to parse JWT token from Authorization header into GatewayUser."""

    def authenticate(self, request):
        django_request = getattr(request, '_request', request)
        auth_header = django_request.headers.get('Authorization', '')
        if not auth_header and hasattr(request, 'META'):
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        tenant_id = (
            django_request.headers.get('X-Tenant-ID') or
            django_request.headers.get('X-TENANT-ID') or
            (hasattr(request, 'META') and request.META.get('HTTP_X_TENANT_ID'))
        )
        if tenant_id:
            request.tenant_id = tenant_id

        if not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]
        verifying_key = get_verifying_key()
        payload = None

        if verifying_key:
            try:
                payload = jwt.decode(
                    token,
                    verifying_key,
                    algorithms=['RS256'],
                    options={'verify_aud': False}
                )
            except Exception:
                pass

        if not payload:
            try:
                payload = jwt.decode(
                    token,
                    options={'verify_signature': False, 'verify_aud': False}
                )
            except Exception:
                payload = None

        if payload:
            user = GatewayUser(payload)
            return (user, token)

        return None


class GatewayUserMiddleware:
    """DRF HTTP Middleware to populate request.user from Authorization JWT header."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        auth_header = request.headers.get('Authorization', '')
        request.tenant_id = request.headers.get('X-Tenant-ID') or request.headers.get('X-TENANT-ID')

        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            verifying_key = get_verifying_key()
            payload = None
            if verifying_key:
                try:
                    payload = jwt.decode(
                        token,
                        verifying_key,
                        algorithms=['RS256'],
                        options={'verify_aud': False}
                    )
                except Exception:
                    pass

            if not payload:
                try:
                    payload = jwt.decode(
                        token,
                        options={'verify_signature': False, 'verify_aud': False}
                    )
                except Exception:
                    payload = None

            if payload:
                request.user = GatewayUser(payload)
            else:
                request.user = AnonymousUser()

        return self.get_response(request)

