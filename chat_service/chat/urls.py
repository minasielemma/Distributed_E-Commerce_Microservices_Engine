from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatRoomViewSet, SecureFileDownloadView

router = DefaultRouter()
router.register(r'rooms', ChatRoomViewSet, basename='chatroom')

urlpatterns = [
    path('', include(router.urls)),
    path('rooms/<uuid:room_id>/files/<uuid:file_id>/download/', SecureFileDownloadView.as_asgi() if hasattr(SecureFileDownloadView, 'as_asgi') else SecureFileDownloadView.as_view(), name='secure-file-download'),
]
