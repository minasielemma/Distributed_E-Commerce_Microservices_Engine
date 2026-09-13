from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, BroadcastNotificationView

router = DefaultRouter()
router.register(r'', NotificationViewSet, basename='notification')

urlpatterns = [
    path('broadcast-notification/', BroadcastNotificationView.as_view(), name='broadcast_notification'),
    path('', include(router.urls)),
]
