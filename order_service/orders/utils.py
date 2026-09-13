import jwt as pyjwt
from datetime import datetime, timedelta, timezone
from django.conf import settings


def make_service_token():
    keys_dir = getattr(settings, 'KEYS_DIR', '/shared_keys')
    with open(f"{keys_dir}/jwt_private.pem", 'r') as f:
        private_key = f.read()
    payload = {
        'service': 'order_service',
        'iat': datetime.now(timezone.utc),
        'exp': datetime.now(timezone.utc) + timedelta(minutes=5),
    }
    return pyjwt.encode(payload, private_key, algorithm='RS256')
