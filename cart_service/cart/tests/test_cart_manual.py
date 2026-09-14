import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cart_project.settings')
django.setup()

from django.test import RequestFactory
from cart.views import CartViewSet
from rest_framework.test import APIRequestFactory
from rest_framework.test import force_authenticate
from django.contrib.auth.models import User

# Need to mock user? We don't have django.contrib.auth.models.User maybe.
