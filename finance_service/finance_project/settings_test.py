from finance_project.settings import *

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
    'USER_ID_CLAIM': 'user_id',
}
