import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-catalog-service-secret-key")
DEBUG = True
import re
import django.http.request

django.http.request.host_validation_re = re.compile(
    r"^([a-z0-9._-]+|\[[a-f0-9]*:[a-f0-9:]+\])(:\d+)?$", re.IGNORECASE
)

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'catalog',
    'common',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'catalog_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'catalog_project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'catalog_db'),
        'USER': os.getenv('POSTGRES_USER', 'catalog_user'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'catalog_pass'),
        'HOST': os.getenv('POSTGRES_HOST', 'catalog_db'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
    }
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTStatelessUserAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'common.pagination.StandardPageNumberPagination',
    'PAGE_SIZE': 10,
}

KEYS_DIR = os.getenv("KEYS_DIR", "/shared_keys")
PUBLIC_KEY_PATH = os.path.join(KEYS_DIR, "jwt_public.pem")

verifying_key = None
if os.path.exists(PUBLIC_KEY_PATH):
    with open(PUBLIC_KEY_PATH, 'r') as f:
        verifying_key = f.read()

SIMPLE_JWT = {
    'ALGORITHM': 'RS256',
    'VERIFYING_KEY': verifying_key,
    'USER_ID_CLAIM': 'user_id',
}
