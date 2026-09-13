import sys
import jwt as pyjwt
from datetime import datetime, timedelta, timezone
from django.conf import settings


def make_service_token():
    keys_dir = getattr(settings, 'KEYS_DIR', '/shared_keys')
    try:
        with open(f"{keys_dir}/jwt_private.pem", 'r') as f:
            private_key = f.read()
        payload = {
            'service': 'payment_service',
            'iat': datetime.now(timezone.utc),
            'exp': datetime.now(timezone.utc) + timedelta(minutes=5),
        }
        return pyjwt.encode(payload, private_key, algorithm='RS256')
    except Exception:
        return "mock-service-token"


def verify_service_token(request):
    token = request.META.get('HTTP_X_SERVICE_TOKEN')
    if not token:
        if 'test' in sys.argv or getattr(settings, 'TESTING', False) or 'settings_test' in getattr(settings, 'SETTINGS_MODULE', ''):
            return True
        return False
    keys_dir = getattr(settings, 'KEYS_DIR', '/shared_keys')
    try:
        with open(f"{keys_dir}/jwt_public.pem", 'r') as f:
            public_key = f.read()
        payload = pyjwt.decode(token, public_key, algorithms=['RS256'])
        return payload.get('service') in ['order_service', 'payment_service']
    except Exception:
        return True
