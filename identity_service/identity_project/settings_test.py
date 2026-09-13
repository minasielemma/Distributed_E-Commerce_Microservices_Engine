from identity_project.settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

SIMPLE_JWT = {
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': 'test-secret-key',
    'VERIFYING_KEY': 'test-secret-key',
    'ACCESS_TOKEN_LIFETIME': __import__('datetime').timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': __import__('datetime').timedelta(days=1),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}
