import logging
import requests
from django.conf import settings
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models.chat import Conversation, Message
from .models.order import Order
from .chat_serializers import (
    ConversationSerializer,
    ConversationDetailSerializer,
    CreateConversationSerializer,
    MessageSerializer,
)

logger = logging.getLogger(__name__)


def send_notification_to_identity(user_id, tenant_id, title, message, notif_type='CHAT', metadata=None):
    try:
        identity_url = getattr(settings, 'IDENTITY_SERVICE_URL', 'http://identity_service:8000')
        payload = {
            'user_id': str(user_id) if user_id else None,
            'tenant_id': str(tenant_id) if tenant_id else None,
            'title': title,
            'message': message,
            'notification_type': notif_type,
            'metadata': metadata or {},
        }
        requests.post(f"{identity_url}/api/notifications/create_internal/", json=payload, timeout=3)
    except Exception as e:
        logger.warning(f"Failed to push notification to identity_service: {e}")


def broadcast_notification_ws(group_name, title, message, notif_type='CHAT', metadata=None):
    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'notification_message',
                    'data': {
                        'title': title,
                        'message': message,
                        'notification_type': notif_type,
                        'metadata': metadata or {},
                    }
                }
            )
    except Exception as e:
        logger.warning(f"Failed to broadcast notification via WS: {e}")


class ConversationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        tenant_id = getattr(self.request, 'tenant_id', None)
        qs = Conversation.objects.all()

        # If user has tenant_id or admin/shop_owner role, show tenant conversations
        is_owner = getattr(user, 'role', '') in ['SHOP_OWNER', 'ADMIN', 'SUPER_ADMIN'] or bool(tenant_id)
        
        if is_owner and tenant_id:
            return qs.filter(tenant_id=tenant_id)
        elif hasattr(user, 'id'):
            return qs.filter(customer_id=user.id)
        return Conversation.objects.none()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ConversationDetailSerializer
        if self.action == 'create':
            return CreateConversationSerializer
        return ConversationSerializer

    def create(self, request, *args, **kwargs):
        serializer = CreateConversationSerializer(data=request.data)
        serializer.is_validate_error = True
        serializer.is_valid(raise_exception=True)

        user = request.user
        tenant_id = getattr(request, 'tenant_id', None)
        order_id = serializer.validated_data.get('order_id')
        subject = serializer.validated_data.get('subject', 'Order Inquiry')
        initial_content = serializer.validated_data['initial_message']

        # Determine tenant_id from order if missing
        if not tenant_id and order_id:
            try:
                order = Order.objects.get(id=order_id)
                tenant_id = order.tenant_id
            except Order.DoesNotExist:
                pass

        if not tenant_id:
            return Response(
                {'detail': 'Tenant ID (X-Tenant-ID header or valid order_id) is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        customer_id = user.id
        customer_name = getattr(user, 'username', '') or getattr(user, 'email', 'Customer')

        conversation = Conversation.objects.create(
            tenant_id=tenant_id,
            customer_id=customer_id,
            customer_name=customer_name,
            order_id=order_id,
            subject=subject,
        )

        msg = Message.objects.create(
            conversation=conversation,
            sender_id=customer_id,
            sender_type='CUSTOMER',
            sender_name=customer_name,
            content=initial_content,
            is_read_by_customer=True,
            is_read_by_owner=False,
        )

        # Notify shop owner / tenant
        send_notification_to_identity(
            user_id=None,
            tenant_id=tenant_id,
            title=f"New Chat Inquiry from {customer_name}",
            message=initial_content[:100],
            notif_type='CHAT',
            metadata={'conversation_id': str(conversation.id)}
        )
        broadcast_notification_ws(
            f"notifications_tenant_{tenant_id}",
            title=f"New Chat Inquiry: {subject}",
            message=initial_content[:100],
            notif_type='CHAT',
            metadata={'conversation_id': str(conversation.id)}
        )

        out_serializer = ConversationDetailSerializer(conversation, context={'request': request})
        return Response(out_serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user

        # Mark messages as read depending on who is viewing
        if str(user.id) == str(instance.customer_id):
            instance.messages.filter(is_read_by_customer=False).update(is_read_by_customer=True)
        else:
            instance.messages.filter(is_read_by_owner=False).update(is_read_by_owner=True)

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='messages')
    def send_message(self, request, pk=None):
        conversation = self.get_object()
        content = request.data.get('content', '').strip()
        if not content:
            return Response({'detail': 'Message content cannot be empty.'}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        sender_id = user.id
        sender_name = getattr(user, 'username', '') or getattr(user, 'email', 'User')

        if str(user.id) == str(conversation.customer_id):
            sender_type = 'CUSTOMER'
            is_read_cust = True
            is_read_owner = False
        else:
            sender_type = 'SHOP_OWNER'
            is_read_cust = False
            is_read_owner = True

        message = Message.objects.create(
            conversation=conversation,
            sender_id=sender_id,
            sender_type=sender_type,
            sender_name=sender_name,
            content=content,
            is_read_by_customer=is_read_cust,
            is_read_by_owner=is_read_owner,
        )

        conversation.save() # Updates auto_now last_message_at

        # Broadcast via Channel Layer to chat room
        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f"chat_{conversation.id}",
                    {
                        'type': 'chat_message',
                        'data': MessageSerializer(message).data
                    }
                )
        except Exception as e:
            logger.warning(f"Failed to broadcast chat_message: {e}")

        # Send notification to recipient
        if sender_type == 'CUSTOMER':
            send_notification_to_identity(
                user_id=None,
                tenant_id=conversation.tenant_id,
                title=f"Chat from {sender_name}",
                message=content[:100],
                notif_type='CHAT',
                metadata={'conversation_id': str(conversation.id)}
            )
            broadcast_notification_ws(
                f"notifications_tenant_{conversation.tenant_id}",
                title=f"New message from {sender_name}",
                message=content[:100],
                notif_type='CHAT',
                metadata={'conversation_id': str(conversation.id)}
            )
        else:
            send_notification_to_identity(
                user_id=conversation.customer_id,
                tenant_id=conversation.tenant_id,
                title="New message from Shop Owner",
                message=content[:100],
                notif_type='CHAT',
                metadata={'conversation_id': str(conversation.id)}
            )
            broadcast_notification_ws(
                f"notifications_{conversation.customer_id}",
                title="New message from Shop Owner",
                message=content[:100],
                notif_type='CHAT',
                metadata={'conversation_id': str(conversation.id)}
            )

        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch'], url_path='close')
    def close_conversation(self, request, pk=None):
        conversation = self.get_object()
        conversation.status = 'CLOSED'
        conversation.save()
        return Response({'detail': 'Conversation closed.', 'status': conversation.status})
