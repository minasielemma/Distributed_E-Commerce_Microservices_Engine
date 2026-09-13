import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notification_project.settings')

django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from common.ws_auth import JWTWebSocketAuthMiddleware
from notification_project.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTWebSocketAuthMiddleware(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
