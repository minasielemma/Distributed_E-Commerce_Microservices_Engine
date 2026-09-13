from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from common.ws_auth import decode_jwt_token
from .models import Notification
from .serializers import NotificationSerializer
from .kafka_producer import publish_notification_event
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def get_authenticated_user(request):
    """Extract authenticated GatewayUser from request header or request.user."""
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        user = decode_jwt_token(token)
        if user and getattr(user, 'is_authenticated', False):
            return user
    if hasattr(request, 'user') and getattr(request.user, 'is_authenticated', False):
        return request.user
    return None


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        user = get_authenticated_user(self.request)
        if not user:
            return Notification.objects.none()
        
        user_id = str(user.id)
        qs = Notification.objects.filter(user_id=user_id)
        
        tenant_id = getattr(user, 'tenant_id', None)
        if tenant_id:
            qs = Notification.objects.filter(user_id=user_id) | Notification.objects.filter(tenant_id=str(tenant_id))
            
        return qs.distinct()

    def list(self, request, *args, **kwargs):
        user = get_authenticated_user(request)
        if not user:
            return Response({'detail': 'Authentication credentials were not provided.'}, status=status.HTTP_401_UNAUTHORIZED)
        return super().list(request, *args, **kwargs)

    @action(detail=True, methods=['post', 'patch'], url_path='mark_read')
    def mark_read(self, request, pk=None):
        user = get_authenticated_user(request)
        if not user:
            return Response({'detail': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            notification = Notification.objects.get(id=pk, user_id=str(user.id))
            notification.is_read = True
            notification.save()
            return Response({'status': 'notification marked as read'}, status=status.HTTP_200_OK)
        except Notification.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'], url_path='read')
    def mark_as_read_legacy(self, request, pk=None):
        """Backward compatibility endpoint for legacy mark_as_read."""
        return self.mark_read(request, pk=pk)

    @action(detail=False, methods=['post'], url_path='mark_all_read')
    def mark_all_read(self, request):
        user = get_authenticated_user(request)
        if not user:
            return Response({'detail': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        
        Notification.objects.filter(user_id=str(user.id), is_read=False).update(is_read=True)
        return Response({'status': 'all notifications marked as read'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='unread_count')
    def unread_count(self, request):
        user = get_authenticated_user(request)
        if not user:
            return Response({'unread_count': 0}, status=status.HTTP_200_OK)
        
        count = Notification.objects.filter(user_id=str(user.id), is_read=False).count()
        return Response({'unread_count': count}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='create-internal')
    def create_internal(self, request):
        user_id = request.data.get('user_id')
        tenant_id = request.data.get('tenant_id')
        title = request.data.get('title')
        message = request.data.get('message')
        notification_type = request.data.get('notification_type', 'SYSTEM')
        metadata = request.data.get('metadata', {})

        if not (title and message and (user_id or tenant_id)):
            return Response({'error': 'title, message, and user_id or tenant_id are required.'}, status=status.HTTP_400_BAD_REQUEST)

        payload = {
            'user_id': user_id,
            'tenant_id': tenant_id,
            'title': title,
            'message': message,
            'notification_type': notification_type,
            'metadata': metadata,
        }

        # Send via Kafka
        publish_notification_event('notification.send', payload)

        return Response({'status': 'queued', 'message': 'Notification dispatched to Kafka'}, status=status.HTTP_201_CREATED)


class BroadcastNotificationView(APIView):
    """View for dispatching notifications directly via Kafka or Channel Layer."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        user_ids = request.data.get('user_ids', [])
        user_id = request.data.get('user_id')
        if user_id and not user_ids:
            user_ids = [user_id]
            
        tenant_id = request.data.get('tenant_id')
        title = request.data.get('title')
        message = request.data.get('message')
        notification_type = request.data.get('notification_type', 'SYSTEM')
        metadata = request.data.get('metadata', {})

        if not (title and message):
            return Response({'error': 'title and message are required.'}, status=status.HTTP_400_BAD_REQUEST)

        payload = {
            'recipient_ids': user_ids,
            'tenant_id': tenant_id,
            'title': title,
            'message': message,
            'notification_type': notification_type,
            'metadata': metadata
        }

        success = publish_notification_event('notification.broadcast', payload)
        if success:
            return Response({'status': 'broadcast_dispatched'}, status=status.HTTP_200_OK)
        return Response({'error': 'Failed to publish to Kafka'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
