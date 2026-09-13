import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chat_project.settings')

django_asgi_app = get_asgi_application()

from common.ws_auth import JWTWebSocketAuthMiddleware
from .routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTWebSocketAuthMiddleware(
        URLRouter(websocket_urlpatterns)
    ),
})
