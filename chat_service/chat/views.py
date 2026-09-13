import logging
import requests
from django.conf import settings
from django.http import HttpResponse, StreamingHttpResponse
from rest_framework import status, viewsets, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import ChatRoom, RoomParticipant, ChatMessage
from .serializers import (
    ChatRoomSerializer,
    ChatRoomDetailSerializer,
    CreateChatRoomSerializer,
    AddParticipantSerializer,
    ChatMessageSerializer,
    SendMessageSerializer,
    RoomParticipantSerializer,
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
        headers = {'X-Service-Token': 'internal'}
        res = requests.post(f"{identity_url}/api/auth/notifications/create-internal/", json=payload, headers=headers, timeout=3)
        if res.status_code not in [200, 201]:
            logger.warning(f"Failed to send notification to identity_service: status={res.status_code} body={res.text}")
    except Exception as e:
        logger.warning(f"Failed to send notification to identity_service: {e}")


def ensure_room_participants(room, auth_header=None):
    """Ensure room has store owner or platform admins if missing."""
    if not room:
        return
    try:
        existing_roles = set(RoomParticipant.objects.filter(room=room).values_list('user_role', flat=True))
        needs_owner = (room.tenant_id or room.order_id or room.room_type == 'ORDER_SUPPORT') and not (
            'STORE_OWNER' in existing_roles or 'SHOP_OWNER' in existing_roles or 'TENANT_ADMIN' in existing_roles
        )
        needs_admin = (room.room_type in ['SUPPORT', 'CUSTOMER_SUPPORT'] or 'support' in str(room.name).lower()) and not (
            'PLATFORM_ADMIN' in existing_roles or 'ADMIN' in existing_roles
        )

        if needs_owner or needs_admin:
            auto_add_participants(
                room=room,
                creator_user_id=room.created_by,
                tenant_id=room.tenant_id,
                order_id=room.order_id,
                room_type=room.room_type,
                auth_header=auth_header
            )
    except Exception as e:
        logger.warning(f"Failed in ensure_room_participants for room {room.id}: {e}")


def sync_media_file_sharing(media_file_id, user_ids, auth_header=None):
    """Sync chat room participants into shared_with_users field of MediaFile in media_service."""
    if not media_file_id or not user_ids:
        return
    try:
        media_service_url = getattr(settings, 'MEDIA_SERVICE_URL', 'http://media_service:8000')
        target_url = f"{media_service_url}/api/media/files/{media_file_id}/share/"
        headers = {}
        if auth_header:
            headers['Authorization'] = auth_header
        payload = {
            'visibility': 'SHARED',
            'shared_with_users': [str(u) for u in user_ids]
        }
        resp = requests.post(target_url, json=payload, headers=headers, timeout=5)
        if resp.status_code != 200:
            logger.warning(f"Failed to update media file sharing for {media_file_id}: {resp.text}")
    except Exception as e:
        logger.warning(f"Exception syncing media file sharing for {media_file_id}: {e}")


def broadcast_room_ws(room_id, event_type, data):
    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            if isinstance(data, dict):
                data['room_id'] = str(room_id)
                data['room'] = str(room_id)
            async_to_sync(channel_layer.group_send)(
                f"chat_room_{room_id}",
                {
                    'type': event_type,
                    'room_id': str(room_id),
                    'data': data
                }
            )
    except Exception as e:
        logger.warning(f"Failed to broadcast to channel layer: {e}")


def get_user_total_unread_count(user_id):
    if not user_id:
        return 0
    from .models import ChatMessage, RoomParticipant
    room_ids = RoomParticipant.objects.filter(user_id=user_id).values_list('room_id', flat=True)
    return ChatMessage.objects.filter(
        room_id__in=room_ids,
        is_deleted=False
    ).exclude(
        sender_id=user_id
    ).exclude(
        recipient_statuses__user_id=user_id,
        recipient_statuses__status='READ'
    ).count()


def get_user_room_unread_count(user_id, room_id):
    if not user_id or not room_id:
        return 0
    from .models import ChatMessage
    return ChatMessage.objects.filter(
        room_id=room_id,
        is_deleted=False
    ).exclude(
        sender_id=user_id
    ).exclude(
        recipient_statuses__user_id=user_id,
        recipient_statuses__status='READ'
    ).count()


def broadcast_user_update(user_id, event_type, data):
    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f"user_updates_{user_id}",
                {
                    'type': 'user_update_event',
                    'event': event_type,
                    'data': data
                }
            )
    except Exception as e:
        logger.warning(f"Failed to broadcast user update to {user_id}: {e}")


def notify_room_participants_update(room, event_type='room_updated', msg=None):
    try:
        from .models import RoomParticipant
        participants = RoomParticipant.objects.filter(room=room)
        for p in participants:
            u_id = p.user_id
            room_unread = get_user_room_unread_count(u_id, room.id)
            total_unread = get_user_total_unread_count(u_id)

            last_msg_data = None
            if msg:
                content_text = msg.content[:100] if msg.content else ('[Attachment]' if msg.media_file_id else 'New message')
                last_msg_data = {
                    'id': str(msg.id),
                    'content': content_text,
                    'sender_id': str(msg.sender_id),
                    'sender_name': msg.sender_name,
                    'created_at': msg.created_at.isoformat()
                }

            data = {
                'room_id': str(room.id),
                'name': room.name,
                'room_type': room.room_type,
                'last_message': last_msg_data,
                'last_message_at': (msg.created_at.isoformat() if msg else (room.last_message_at.isoformat() if room.last_message_at else None)),
                'unread_count': room_unread,
                'total_unread_count': total_unread
            }
            broadcast_user_update(u_id, event_type, data)
    except Exception as e:
        logger.warning(f"Failed to notify room participants update for room {room.id}: {e}")

def auto_add_participants(room, creator_user_id, tenant_id=None, order_id=None, room_type='DIRECT', auth_header=None):
    """
    Automatically add appropriate participants based on room type and context:
    - SUPPORT / CUSTOMER_SUPPORT: Auto-add Platform Admins from identity_service.
    - ORDER_SUPPORT or order_id / tenant_id present: Auto-add Store Owner / Tenant Owner from identity_service.
    """
    identity_url = getattr(settings, 'IDENTITY_SERVICE_URL', 'http://identity_service:8000')
    added_names = []
    headers = {'X-Service-Token': 'internal'}
    if auth_header:
        headers['Authorization'] = auth_header

    # 1. Handle Support Chat Rooms (Auto-add Platform Admins)
    is_support = (room_type in ['SUPPORT', 'CUSTOMER_SUPPORT'] or 'support' in str(room.name).lower())
    if is_support:
        try:
            res = requests.get(f"{identity_url}/api/auth/users/lookup/?role=PLATFORM_ADMIN", headers=headers, timeout=3)
            if res.status_code == 200:
                admin_data = res.json()
                admins = admin_data.get('results', [])
                for adm in admins:
                    adm_id = adm.get('id')
                    if adm_id and str(adm_id) != str(creator_user_id):
                        p, created = RoomParticipant.objects.get_or_create(
                            room=room,
                            user_id=adm_id,
                            defaults={
                                'user_name': adm.get('username') or 'Support Admin',
                                'user_role': adm.get('role', 'PLATFORM_ADMIN'),
                                'role': 'ADMIN'
                            }
                        )
                        if created:
                            added_names.append(adm.get('username') or 'Support Admin')
        except Exception as e:
            logger.warning(f"Failed to auto-add admins to support room {room.id}: {e}")

    # 2. Handle Order-Related Chat Rooms (Auto-add Store Owner)
    target_tenant_id = tenant_id
    if not target_tenant_id and order_id:
        try:
            order_url = getattr(settings, 'ORDER_SERVICE_URL', 'http://order_service:8000')
            o_res = requests.get(f"{order_url}/api/orders/{order_id}/", headers=headers, timeout=3)
            if o_res.status_code == 200:
                o_data = o_res.json()
                target_tenant_id = o_data.get('tenant_id')
                if target_tenant_id and not room.tenant_id:
                    room.tenant_id = target_tenant_id
                    room.save(update_fields=['tenant_id'])
            else:
                logger.warning(f"Failed to fetch order {order_id}: status={o_res.status_code} body={o_res.text}")
        except Exception as e:
            logger.warning(f"Failed to resolve order {order_id} tenant_id: {e}")

    is_order_chat = (room_type == 'ORDER_SUPPORT' or order_id or target_tenant_id)
    if is_order_chat and target_tenant_id:
        try:
            res = requests.get(f"{identity_url}/api/auth/users/lookup/?tenant_id={target_tenant_id}", headers=headers, timeout=3)
            if res.status_code == 200:
                owner_data = res.json()
                owners = owner_data.get('results', [])
                for own in owners:
                    own_id = own.get('id')
                    if own_id and str(own_id) != str(creator_user_id):
                        p, created = RoomParticipant.objects.get_or_create(
                            room=room,
                            user_id=own_id,
                            defaults={
                                'user_name': own.get('username') or 'Store Owner',
                                'user_role': own.get('role', 'STORE_OWNER'),
                                'role': 'ADMIN'
                            }
                        )
                        if created:
                            added_names.append(own.get('username') or 'Store Owner')
            else:
                logger.warning(f"Failed to lookup tenant owner for {target_tenant_id}: status={res.status_code} body={res.text}")
        except Exception as e:
            logger.warning(f"Failed to auto-add store owner for tenant {target_tenant_id}: {e}")

    return added_names


class ChatRoomViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not hasattr(user, 'id'):
            return ChatRoom.objects.none()

        user_id = user.id
        tenant_id = (
            getattr(self.request, 'tenant_id', None)
            or getattr(user, 'tenant_id', None)
            or self.request.headers.get('X-Tenant-Id')
            or self.request.headers.get('X-TENANT-ID')
        )

        user_room_ids = RoomParticipant.objects.filter(user_id=user_id).values_list('room_id', flat=True)

        user_role = str(getattr(user, 'role', '')).upper()
        is_platform_admin = (
            user_role in ['PLATFORM_ADMIN', 'SUPER_ADMIN'] or
            getattr(user, 'is_superuser', False) or
            getattr(user, 'is_platform_admin', False)
        )
        is_store_owner = user_role in ['STORE_OWNER', 'SHOP_OWNER', 'TENANT_ADMIN', 'OWNER', 'VENDOR']

        if is_platform_admin:
            if tenant_id:
                qs = ChatRoom.objects.filter(tenant_id=tenant_id, is_active=True)
            else:
                qs = ChatRoom.objects.filter(is_active=True)
        elif is_store_owner and tenant_id:
            from django.db.models import Q
            qs = ChatRoom.objects.filter(Q(id__in=user_room_ids) | Q(tenant_id=tenant_id), is_active=True)
        else:
            qs = ChatRoom.objects.filter(id__in=user_room_ids, is_active=True)

        return qs.distinct()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ChatRoomDetailSerializer
        if self.action == 'create':
            return CreateChatRoomSerializer
        return ChatRoomSerializer

    def create(self, request, *args, **kwargs):
        serializer = CreateChatRoomSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        tenant_id = serializer.validated_data.get('tenant_id') or getattr(request, 'tenant_id', None)
        name = serializer.validated_data.get('name', 'Chat Room')
        room_type = serializer.validated_data.get('room_type', 'DIRECT')
        order_id = serializer.validated_data.get('order_id')
        participant_user_ids = serializer.validated_data.get('participant_user_ids', [])
        initial_content = serializer.validated_data.get('initial_message', '')

        creator_name = getattr(user, 'username', '') or getattr(user, 'email', 'User')
        creator_role = getattr(user, 'role', 'MEMBER')

        # Room deduplication: reuse existing active room if available for order_id
        if order_id:
            existing_room = ChatRoom.objects.filter(order_id=order_id, is_active=True).first()
            if existing_room:
                room = existing_room
                RoomParticipant.objects.get_or_create(
                    room=room,
                    user_id=user.id,
                    defaults={'user_name': creator_name, 'user_role': creator_role, 'role': 'OWNER'}
                )
                auth_header = request.headers.get('Authorization')
                auto_add_participants(
                    room=room,
                    creator_user_id=user.id,
                    tenant_id=tenant_id or room.tenant_id,
                    order_id=order_id,
                    room_type=room_type,
                    auth_header=auth_header
                )
                if initial_content:
                    msg = ChatMessage.objects.create(
                        room=room,
                        sender_id=user.id,
                        sender_name=creator_name,
                        sender_role=creator_role,
                        content=initial_content,
                        message_type='TEXT'
                    )
                    from .models import create_recipient_statuses_for_message
                    create_recipient_statuses_for_message(msg)
                    msg_data = ChatMessageSerializer(msg).data
                    broadcast_room_ws(room.id, 'new_message_event', msg_data)

                out_serializer = ChatRoomDetailSerializer(room, context={'request': request})
                return Response(out_serializer.data, status=status.HTTP_200_OK)

        room = ChatRoom.objects.create(
            tenant_id=tenant_id,
            name=name,
            room_type=room_type,
            order_id=order_id,
            created_by=user.id,
        )

        # Add creator as OWNER participant
        RoomParticipant.objects.create(
            room=room,
            user_id=user.id,
            user_name=creator_name,
            user_role=creator_role,
            role='OWNER'
        )

        # Add initial invited participants
        for uid in participant_user_ids:
            if str(uid) != str(user.id):
                u_name = f'User-{str(uid)[:6]}'
                try:
                    from django.conf import settings
                    identity_url = getattr(settings, 'IDENTITY_SERVICE_URL', 'http://identity_service:8000')
                    u_res = requests.get(f"{identity_url}/api/auth/users/lookup/?user_id={uid}", headers={'X-Service-Token': 'internal'}, timeout=2)
                    if u_res.status_code == 200:
                        u_data = u_res.json().get('results', [])
                        if u_data:
                            u_name = u_data[0].get('username') or u_name
                except Exception:
                    pass

                RoomParticipant.objects.get_or_create(
                    room=room,
                    user_id=uid,
                    defaults={'user_name': u_name, 'role': 'MEMBER'}
                )

        # Automatically resolve and add support admins or store owners
        auth_header = request.headers.get('Authorization')
        auto_added = auto_add_participants(
            room=room,
            creator_user_id=user.id,
            tenant_id=tenant_id,
            order_id=order_id,
            room_type=room_type,
            auth_header=auth_header
        )

        # Send initial message if provided
        msg = None
        if initial_content:
            msg = ChatMessage.objects.create(
                room=room,
                sender_id=user.id,
                sender_name=creator_name,
                sender_role=creator_role,
                content=initial_content,
                message_type='TEXT'
            )
            from .models import create_recipient_statuses_for_message
            create_recipient_statuses_for_message(msg)

        notify_room_participants_update(room, event_type='room_created', msg=msg)

        out_serializer = ChatRoomDetailSerializer(room, context={'request': request})
        return Response(out_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='participants')
    def add_participant(self, request, pk=None):
        room = self.get_object()
        user = request.user
        user_id_str = str(getattr(user, 'id', ''))

        # 1. Check direct room 2-participant limit
        if room.room_type == 'DIRECT' and RoomParticipant.objects.filter(room=room).count() >= 2:
            return Response(
                {'error': 'Direct chat rooms cannot have more than 2 participants.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Check authorization criteria:
        is_room_creator = (str(room.created_by) == user_id_str)
        requester_participant = RoomParticipant.objects.filter(room=room, user_id=user.id).first() if hasattr(user, 'id') else None
        is_room_admin_or_owner = bool(requester_participant and requester_participant.role in ['OWNER', 'ADMIN'])

        user_role = str(getattr(user, 'role', '')).upper()
        is_platform_admin = (
            user_role in ['PLATFORM_ADMIN', 'SUPER_ADMIN'] or
            getattr(user, 'is_superuser', False) or
            getattr(user, 'is_platform_admin', False)
        )

        user_perms = getattr(user, 'permissions', []) or []
        has_add_perm = (
            'chat.add_participant' in user_perms or
            'add_participant' in user_perms or
            (hasattr(user, 'has_perm') and user.has_perm('chat.add_participant'))
        )

        if not (is_room_creator or is_room_admin_or_owner or is_platform_admin or has_add_perm):
            return Response(
                {'error': 'Only the chat room owner, admin, or user with permission can add participants.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AddParticipantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_input = serializer.validated_data.get('username') or serializer.validated_data.get('user_id')
        user_role = serializer.validated_data.get('user_role', 'MEMBER')
        role = serializer.validated_data.get('role', 'MEMBER')

        import uuid
        target_user_id = None
        user_name = serializer.validated_data.get('user_name') or user_input

        try:
            uuid.UUID(str(user_input))
            target_user_id = str(user_input)
        except (ValueError, TypeError):
            target_user_id = None

        if not target_user_id or not user_name or user_name == target_user_id:
            try:
                identity_url = getattr(settings, 'IDENTITY_SERVICE_URL', 'http://identity_service:8000')
                param = f"username={user_input}" if not target_user_id else f"user_id={target_user_id}"
                headers = {'X-Service-Token': 'internal'}
                if request.headers.get('Authorization'):
                    headers['Authorization'] = request.headers['Authorization']
                res = requests.get(f"{identity_url}/api/auth/users/lookup/?{param}", headers=headers, timeout=3)
                if res.status_code == 200:
                    data = res.json()
                    target_user_id = data['id']
                    user_name = data['username']
                    user_role = data.get('role', 'MEMBER')
                else:
                    return Response({'error': f"User '{user_input}' not found in system."}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                logger.warning(f"Failed to lookup user in identity_service: {e}")
                if not target_user_id:
                    return Response({'error': f"Could not resolve user '{user_input}'."}, status=status.HTTP_400_BAD_REQUEST)

        participant, created = RoomParticipant.objects.get_or_create(
            room=room,
            user_id=target_user_id,
            defaults={'user_name': user_name, 'user_role': user_role, 'role': role}
        )

        if not created:
            participant.user_name = user_name
            participant.role = role
            participant.save()

        sys_msg = ChatMessage.objects.create(
            room=room,
            sender_id=request.user.id,
            sender_name='SYSTEM',
            content=f"{user_name} was added to the chat room.",
            message_type='SYSTEM'
        )

        broadcast_room_ws(room.id, 'new_message_event', ChatMessageSerializer(sys_msg).data)

        # Update media_service shared_with_users for all room attachments
        all_room_participant_ids = list(RoomParticipant.objects.filter(room=room).values_list('user_id', flat=True))
        room_media_ids = ChatMessage.objects.filter(room=room, media_file_id__isnull=False).values_list('media_file_id', flat=True)
        auth_header = request.headers.get('Authorization')
        for m_id in set(room_media_ids):
            sync_media_file_sharing(m_id, all_room_participant_ids, auth_header)

        send_notification_to_identity(
            user_id=target_user_id,
            tenant_id=room.tenant_id,
            title=f"Added to Chat Room '{room.name}'",
            message=f"You were added to {room.name} by {request.user.username}",
            notif_type='CHAT',
            metadata={'room_id': str(room.id)}
        )

        return Response(RoomParticipantSerializer(participant).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path='participants/(?P<user_id>[^/.]+)')
    def remove_participant(self, request, pk=None, user_id=None):
        room = self.get_object()
        user = request.user
        user_id_str = str(getattr(user, 'id', ''))

        # Check authorization criteria:
        # 1. Self-removal (leaving the room)
        is_self = (str(user_id) == user_id_str)

        # 2. Chat room creator / owner
        is_room_creator = (str(room.created_by) == user_id_str)

        # 3. Room participant with OWNER or ADMIN role
        requester_participant = RoomParticipant.objects.filter(room=room, user_id=user.id).first() if hasattr(user, 'id') else None
        is_room_admin_or_owner = bool(requester_participant and requester_participant.role in ['OWNER', 'ADMIN'])

        # 4. Platform admin or explicit permission check
        user_role = str(getattr(user, 'role', '')).upper()
        is_platform_admin = (
            user_role in ['PLATFORM_ADMIN', 'SUPER_ADMIN'] or
            getattr(user, 'is_superuser', False) or
            getattr(user, 'is_platform_admin', False)
        )

        user_perms = getattr(user, 'permissions', []) or []
        has_remove_perm = (
            'chat.remove_participant' in user_perms or
            'remove_participant' in user_perms or
            (hasattr(user, 'has_perm') and user.has_perm('chat.remove_participant'))
        )

        if not (is_self or is_room_creator or is_room_admin_or_owner or is_platform_admin or has_remove_perm):
            return Response(
                {'error': 'Only the chat room owner, admin, or user with permission can remove participants.'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            participant = RoomParticipant.objects.get(room=room, user_id=user_id)
            user_name = participant.user_name
            participant.delete()

            sys_msg = ChatMessage.objects.create(
                room=room,
                sender_id=request.user.id,
                sender_name='SYSTEM',
                content=f"{user_name} left the chat room.",
                message_type='SYSTEM'
            )
            broadcast_room_ws(room.id, 'new_message_event', ChatMessageSerializer(sys_msg).data)
            return Response({'detail': 'Participant removed.'}, status=status.HTTP_200_OK)
        except RoomParticipant.DoesNotExist:
            return Response({'error': 'Participant not found in room.'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get', 'post'], url_path='messages')
    def messages_action(self, request, pk=None):
        room = self.get_object()
        user = request.user

        auth_header = request.headers.get('Authorization')
        ensure_room_participants(room, auth_header=auth_header)

        user_role = str(getattr(user, 'role', '')).upper()
        is_platform_admin = (
            user_role in ['PLATFORM_ADMIN', 'SUPER_ADMIN'] or
            getattr(user, 'is_superuser', False) or
            getattr(user, 'is_platform_admin', False)
        )
        is_store_owner = user_role in ['STORE_OWNER', 'SHOP_OWNER', 'TENANT_ADMIN', 'OWNER', 'VENDOR']
        user_tenant_id = (
            getattr(user, 'tenant_id', None)
            or request.headers.get('X-Tenant-Id')
            or request.headers.get('X-TENANT-ID')
        )
        is_tenant_owner_access = is_store_owner and user_tenant_id and str(room.tenant_id) == str(user_tenant_id)

        is_participant = RoomParticipant.objects.filter(room=room, user_id=user.id).exists() if hasattr(user, 'id') else False

        if not (is_participant or is_platform_admin or is_tenant_owner_access):
            return Response({'error': 'You are not a participant in this chat room.'}, status=status.HTTP_403_FORBIDDEN)

        if request.method == 'GET':
            before_id = request.query_params.get('before_id')
            limit = int(request.query_params.get('limit', 20))
            qs = ChatMessage.objects.filter(room=room, is_deleted=False).prefetch_related('recipient_statuses', 'reactions').order_by('-created_at')
            if before_id:
                try:
                    anchor = ChatMessage.objects.get(id=before_id)
                    qs = qs.filter(created_at__lt=anchor.created_at)
                except (ChatMessage.DoesNotExist, ValueError, AttributeError, TypeError):
                    pass
            messages = list(qs[:limit])
            messages.reverse()
            serializer = ChatMessageSerializer(messages, many=True, context={'request': request})
            return Response({
                'room_id': str(room.id),
                'messages': serializer.data,
                'has_more': qs.count() > limit
            }, status=status.HTTP_200_OK)

        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        content = serializer.validated_data.get('content', '')
        media_file_id = serializer.validated_data.get('media_file_id')

        message_type = 'FILE' if media_file_id else 'TEXT'

        # Sync room participants to shared_with_users in media_service if file attached
        if media_file_id:
            participant_user_ids = list(RoomParticipant.objects.filter(room=room).values_list('user_id', flat=True))
            auth_header = request.headers.get('Authorization')
            sync_media_file_sharing(media_file_id, participant_user_ids, auth_header)

        message = ChatMessage.objects.create(
            room=room,
            sender_id=user.id,
            sender_name=getattr(user, 'username', 'User'),
            sender_role=getattr(user, 'role', 'MEMBER'),
            content=content,
            message_type=message_type,
            media_file_id=media_file_id
        )

        from .models import create_recipient_statuses_for_message
        create_recipient_statuses_for_message(message)

        room.save()

        msg_data = ChatMessageSerializer(message).data
        broadcast_room_ws(room.id, 'new_message_event', msg_data)

        other_participants = RoomParticipant.objects.filter(room=room).exclude(user_id=user.id)
        for p in other_participants:
            send_notification_to_identity(
                user_id=p.user_id,
                tenant_id=room.tenant_id,
                title=f"New Message in '{room.name}'",
                message=f"{getattr(user, 'username', 'User')}: {content[:80]}" if content else f"{getattr(user, 'username', 'User')} shared a file",
                notif_type='CHAT',
                metadata={
                    'room_id': str(room.id),
                    'message_id': str(message.id),
                    'content': content,
                    'sender_id': str(user.id),
                    'sender_name': getattr(user, 'username', 'User'),
                    'created_at': message.created_at.isoformat() if hasattr(message.created_at, 'isoformat') else str(message.created_at)
                }
            )

        notify_room_participants_update(room, event_type='room_updated', msg=message)

        return Response(msg_data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='mark_read')
    def mark_read(self, request, pk=None):
        room = self.get_object()
        from django.utils import timezone
        from .models import update_recipient_statuses_for_user
        now = timezone.now()
        user_id = getattr(request.user, 'id', None)
        if not user_id:
            return Response({'error': 'User ID required.'}, status=status.HTTP_400_BAD_REQUEST)

        message_ids = request.data.get('message_ids', [])
        affected_ids = update_recipient_statuses_for_user(room.id, user_id, 'READ', message_ids)

        room_ids = RoomParticipant.objects.filter(user_id=user_id).values_list('room_id', flat=True)
        unread_count = ChatMessage.objects.filter(
            room_id__in=room_ids,
            is_deleted=False
        ).exclude(
            sender_id=user_id
        ).exclude(
            recipient_statuses__user_id=user_id,
            recipient_statuses__status='READ'
        ).count()

        read_data = {
            'room_id': str(room.id),
            'user_id': str(user_id),
            'message_ids': affected_ids,
            'read_at': now.isoformat(),
            'unread_count': unread_count
        }
        broadcast_room_ws(room.id, 'read_receipt_event', read_data)
        notify_room_participants_update(room, event_type='unread_count_update', msg=None)

        return Response({
            'detail': 'Messages marked as read.',
            'count': len(affected_ids),
            'affected_ids': affected_ids,
            'unread_count': unread_count
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='mark_delivered')
    def mark_delivered(self, request, pk=None):
        room = self.get_object()
        from django.utils import timezone
        from .models import update_recipient_statuses_for_user
        now = timezone.now()
        user_id = getattr(request.user, 'id', None)
        if not user_id:
            return Response({'error': 'User ID required.'}, status=status.HTTP_400_BAD_REQUEST)

        message_ids = request.data.get('message_ids', [])
        affected_ids = update_recipient_statuses_for_user(room.id, user_id, 'DELIVERED', message_ids)

        deliv_data = {
            'room_id': str(room.id),
            'user_id': str(user_id),
            'message_ids': affected_ids,
            'delivered_at': now.isoformat()
        }
        broadcast_room_ws(room.id, 'delivery_receipt_event', deliv_data)

        return Response({
            'detail': 'Messages marked as delivered.',
            'count': len(affected_ids),
            'affected_ids': affected_ids
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='react')
    def toggle_reaction(self, request, pk=None):
        room = self.get_object()
        user = request.user
        message_id = request.data.get('message_id')
        emoji = request.data.get('emoji', '👍')

        if not message_id:
            return Response({'error': 'message_id required.'}, status=status.HTTP_400_BAD_REQUEST)

        from .models import ChatMessage, Reaction
        try:
            msg = ChatMessage.objects.get(id=message_id, room=room)
            reaction, created = Reaction.objects.get_or_create(
                message=msg,
                user_id=user.id,
                emoji=emoji,
                defaults={'user_name': getattr(user, 'username', 'User')}
            )
            action_type = 'ADDED'
            if not created:
                reaction.delete()
                action_type = 'REMOVED'

            reaction_data = {
                'message_id': str(message_id),
                'room_id': str(room.id),
                'room': str(room.id),
                'user_id': str(user.id),
                'user_name': getattr(user, 'username', 'User'),
                'emoji': emoji,
                'action': action_type
            }

            broadcast_room_ws(room.id, 'reaction_update_event', reaction_data)
            return Response(reaction_data, status=status.HTTP_200_OK)
        except ChatMessage.DoesNotExist:
            return Response({'error': 'Message not found in this room.'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'], url_path='unread_count')
    def total_unread_count(self, request):
        user_id = getattr(request.user, 'id', None)
        if not user_id:
            return Response({'unread_count': 0}, status=status.HTTP_200_OK)

        room_ids = RoomParticipant.objects.filter(user_id=user_id).values_list('room_id', flat=True)
        count = ChatMessage.objects.filter(
            room_id__in=room_ids,
            is_deleted=False
        ).exclude(
            sender_id=user_id
        ).exclude(
            recipient_statuses__user_id=user_id,
            recipient_statuses__status='READ'
        ).count()

        return Response({'unread_count': count}, status=status.HTTP_200_OK)


class SecureFileDownloadView(views.APIView):
    """Securely serve shared files strictly to verified room participants via media_service."""
    permission_classes = [IsAuthenticated]

    def get(self, request, room_id, file_id):
        user = request.user
        if not hasattr(user, 'id'):
            return Response({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

        is_participant = RoomParticipant.objects.filter(room_id=room_id, user_id=user.id).exists()
        user_role = str(getattr(user, 'role', '')).upper()
        is_admin = (
            user_role in ['ADMIN', 'SUPER_ADMIN', 'PLATFORM_ADMIN', 'STORE_OWNER', 'SHOP_OWNER'] or
            getattr(user, 'is_staff', False) or
            getattr(user, 'is_superuser', False) or
            getattr(user, 'is_platform_admin', False)
        )


        if not (is_participant or is_admin):
            return Response(
                {'error': 'Access Denied: You are not a participant in this chat room.'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            media_service_url = getattr(settings, 'MEDIA_SERVICE_URL', 'http://media_service:8000')
            target_url = f"{media_service_url}/api/media/files/{file_id}/download/"
            headers = {}
            if request.headers.get('Authorization'):
                headers['Authorization'] = request.headers['Authorization']

            resp = requests.get(target_url, headers=headers, stream=True, timeout=10)
            if resp.status_code == 200:
                response = StreamingHttpResponse(
                    resp.iter_content(chunk_size=8192),
                    content_type=resp.headers.get('Content-Type', 'application/octet-stream')
                )
                if resp.headers.get('Content-Disposition'):
                    response['Content-Disposition'] = resp.headers['Content-Disposition']
                return response
            else:
                return Response({'error': 'Failed to retrieve file from media service.'}, status=resp.status_code)
        except Exception as e:
            logger.error(f"Failed to fetch file from media_service: {e}")
            return Response({'error': 'Media service unreachable.'}, status=status.HTTP_502_BAD_GATEWAY)
