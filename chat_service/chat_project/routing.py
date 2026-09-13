from django.urls import re_path
from chat.consumers import ChatRoomConsumer, UserUpdatesConsumer

websocket_urlpatterns = [
    re_path(r'^ws/chat/updates/$', UserUpdatesConsumer.as_asgi()),
    re_path(r'^ws/chat/room/(?P<room_id>[^/]+)/$', ChatRoomConsumer.as_asgi()),
    re_path(r'^ws/chat/(?P<room_id>[^/]+)/$', ChatRoomConsumer.as_asgi()),
]
