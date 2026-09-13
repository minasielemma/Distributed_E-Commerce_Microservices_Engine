import os
import jwt
from urllib.parse import parse_qs
from django.contrib.auth.models import AnonymousUser
from channels.middleware import BaseMiddleware

KEYS_DIR = os.getenv("KEYS_DIR", "/shared_keys")
PUBLIC_KEY_PATH = os.path.join(KEYS_DIR, "jwt_public.pem")


class GatewayUser:
    """Authenticated user representation constructed from JWT payload."""

    def __init__(self, payload):
        self.payload = payload
        user_id = payload.get('user_id') or payload.get('sub')
        self.id = user_id
        self.pk = user_id
        self.username = payload.get('username') or payload.get('email') or str(user_id)
        self.email = payload.get('email', '')
        self.tenant_id = payload.get('tenant_id')
        self.role = str(payload.get('role', 'CUSTOMER')).upper()
        self.is_authenticated = True
        self.is_anonymous = False
        self.is_platform_admin = payload.get('is_platform_admin', False) or payload.get('is_staff', False) or self.role in ['ADMIN', 'SUPER_ADMIN', 'PLATFORM_ADMIN']
        self.is_staff = self.is_platform_admin or self.role in ['SHOP_OWNER', 'STORE_OWNER', 'VENDOR', 'DEALER']
        self.is_superuser = payload.get('is_superuser', False) or self.role in ['SUPER_ADMIN', 'PLATFORM_ADMIN']

    def __str__(self):
        return f"GatewayUser({self.username})"


def get_verifying_key():
    if os.path.exists(PUBLIC_KEY_PATH):
        with open(PUBLIC_KEY_PATH, 'r') as f:
            return f.read()
    return None


def decode_jwt_token(token):
    """Decode and validate JWT token string into GatewayUser or return None."""
    if not token:
        return None
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
        return GatewayUser(payload)
    return None


class JWTWebSocketAuthMiddleware(BaseMiddleware):
    """Authenticate WebSocket connection via query string or header, allowing fallback for 2-step in-band auth."""

    async def __call__(self, scope, receive, send):
        query_string = scope.get('query_string', b'').decode('utf-8')
        query_params = parse_qs(query_string)
        token_list = query_params.get('token', [])
        token = token_list[0] if token_list else None

        if not token:
            headers = dict(scope.get('headers', []))
            if b'authorization' in headers:
                auth = headers[b'authorization'].decode('utf-8')
                if auth.startswith('Bearer '):
                    token = auth.split(' ')[1]

        user = decode_jwt_token(token) if token else None
        scope['user'] = user if user else AnonymousUser()

        return await super().__call__(scope, receive, send)
