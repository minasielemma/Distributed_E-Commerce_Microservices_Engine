import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'identity_project.settings')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
u = User.objects.first()
if u:
    from rest_framework_simplejwt.tokens import RefreshToken
    token = RefreshToken.for_user(u)
    print(str(token.access_token))
