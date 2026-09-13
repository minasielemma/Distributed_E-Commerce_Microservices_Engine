import json
import logging
from datetime import datetime, timezone
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async

from .presence import set_user_online, set_user_offline, get_user_presence, broadcast_presence_event

logger = logging.getLogger(__name__)


class ChatRoomConsumer(AsyncJsonWebsocketConsumer):
    """Room-level real-time WebSocket consumer implementing 2-step in-band authentication and action-based JSON protocol."""

    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs'].get('room_id')
        self.room_group_name = f"chat_room_{self.room_id}"
        self.user = self.scope.get('user')
        self.is_authenticated = False

        await self.accept()

        if self.user and getattr(self.user, 'is_authenticated', False):
            is_allowed = await self.check_participant_access(self.room_id, self.user)
            if not is_allowed:
                logger.warning(f"User {getattr(self.user, 'id', None)} denied WebSocket access to room {self.room_id}")
                await self.close(code=4003)
                return

            self.is_authenticated = True
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.set_online_status('online')

            await self.send_json({
                'type': 'connection_established',
                'status': 'authenticated',
                'data': {
                    'room_id': str(self.room_id),
                    'user_id': str(self.user.id),
                    'message': f"Connected to room {self.room_id}"
                }
            })
        else:
            await self.send_json({
                'type': 'auth_required',
                'data': {
                    'room_id': str(self.room_id),
                    'message': 'Authentication required. Send action: "authenticate" with token payload.'
                }
            })

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive_json(self, content):
        action = content.get('action') or content.get('type')
        payload = content.get('payload', {})

        if action in ['authenticate', 'auth']:
            token = payload.get('token') or content.get('token')
            from common.ws_auth import decode_jwt_token
            user = decode_jwt_token(token) if token else None

            if not user or not getattr(user, 'is_authenticated', False):
                await self.send_json({'type': 'auth_error', 'message': 'Invalid authentication token.'})
                await self.close(code=4001)
                return

            self.user = user
            is_allowed = await self.check_participant_access(self.room_id, self.user)
            if not is_allowed:
                await self.send_json({'type': 'auth_error', 'message': 'Access denied to chat room.'})
                await self.close(code=4003)
                return

            self.is_authenticated = True
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.set_online_status('online')

            await self.send_json({
                'type': 'connection_established',
                'status': 'authenticated',
                'data': {
                    'room_id': str(self.room_id),
                    'user_id': str(self.user.id),
                    'message': f"Authentication successful for room {self.room_id}"
                }
            })
            return

        if not getattr(self, 'is_authenticated', False) or not self.user:
            await self.send_json({'type': 'error', 'message': 'Unauthorized action. Authenticate first.'})
            return

        if action in ['ping', 'heartbeat']:
            await self.set_online_status('online')
            await self.send_json({'type': 'pong', 'data': {'timestamp': datetime.now(timezone.utc).isoformat()}})
            return

        if action == 'send_message':
            text = payload.get('content') or content.get('content', '')
            media_file_id = payload.get('media_file_id') or content.get('media_file_id')

            msg_data = await self.save_message(
                room_id=self.room_id,
                user=self.user,
                content=text,
                media_file_id=media_file_id
            )

            if msg_data:
                # Ensure room_id is always present so clients can filter by room
                if isinstance(msg_data, dict):
                    msg_data['room_id'] = str(self.room_id)
                    if 'room' not in msg_data or not msg_data['room']:
                        msg_data['room'] = str(self.room_id)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'new_message_event',
                        'room_id': str(self.room_id),
                        'sender_channel': self.channel_name,
                        'data': msg_data
                    }
                )

        elif action == 'fetch_messages':
            before_id = payload.get('before_id')
            limit = int(payload.get('limit', 20))
            history_data = await self.get_message_history(self.room_id, before_id, limit)
            await self.send_json({
                'type': 'message_history',
                'data': history_data
            })

        elif action == 'mark_read':
            message_ids = payload.get('message_ids', [])
            read_data = await self.mark_messages_read(self.room_id, self.user.id, message_ids)
            if read_data:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'read_receipt_event',
                        'data': read_data
                    }
                )

        elif action == 'confirm_delivery':
            message_ids = payload.get('message_ids', [])
            delivery_data = await self.mark_messages_delivered(self.room_id, self.user.id, message_ids)
            if delivery_data:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'delivery_receipt_event',
                        'data': delivery_data
                    }
                )

        elif action == 'toggle_reaction':
            message_id = payload.get('message_id')
            emoji = payload.get('emoji', '👍')
            reaction_data = await self.toggle_message_reaction(message_id, self.user, emoji)
            if reaction_data:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'reaction_update_event',
                        'data': reaction_data
                    }
                )

        elif action in ['typing_start', 'typing_stop']:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_event',
                    'data': {
                        'event': action,
                        'user_id': str(self.user.id),
                        'user_name': getattr(self.user, 'username', 'User')
                    }
                }
            )

    async def new_message_event(self, event):
        if event.get('sender_channel') == self.channel_name:
            return
        data = event['data']
        # Guarantee room_id is present in the payload sent to client
        if isinstance(data, dict):
            if not data.get('room_id'):
                data['room_id'] = event.get('room_id', str(self.room_id))
            if not data.get('room'):
                data['room'] = data['room_id']
        await self.send_json({
            'type': 'new_message',
            'data': data
        })

    async def read_receipt_event(self, event):
        data = event['data']
        if isinstance(data, dict):
            data['room_id'] = str(event.get('room_id') or data.get('room_id') or self.room_id)
            data['room'] = data['room_id']
        await self.send_json({
            'type': 'read_receipt',
            'data': data
        })

    async def delivery_receipt_event(self, event):
        data = event['data']
        if isinstance(data, dict):
            data['room_id'] = str(event.get('room_id') or data.get('room_id') or self.room_id)
            data['room'] = data['room_id']
        await self.send_json({
            'type': 'delivery_receipt',
            'data': data
        })

    async def reaction_update_event(self, event):
        data = event['data']
        if isinstance(data, dict):
            data['room_id'] = str(event.get('room_id') or data.get('room_id') or self.room_id)
            data['room'] = data['room_id']
        await self.send_json({
            'type': 'reaction_update',
            'data': data
        })

    async def chat_event(self, event):
        data = event.get('data', {})
        if isinstance(data, dict):
            data['room_id'] = str(event.get('room_id') or data.get('room_id') or self.room_id)
            data['room'] = data['room_id']
        await self.send_json(data)

    # Helper async methods
    @database_sync_to_async
    def set_online_status(self, status):
        if self.user and hasattr(self.user, 'id'):
            set_user_online(self.user.id, status)

    @database_sync_to_async
    def check_participant_access(self, room_id, user):
        from .models import RoomParticipant, ChatRoom
        user_id = getattr(user, 'id', None)
        if not user_id:
            return False

        is_participant = RoomParticipant.objects.filter(room_id=room_id, user_id=user_id).exists()
        if is_participant:
            return True

        user_role = str(getattr(user, 'role', '')).upper()
        is_platform_admin = (
            user_role in ['PLATFORM_ADMIN', 'SUPER_ADMIN'] or
            getattr(user, 'is_superuser', False) or
            getattr(user, 'is_platform_admin', False)
        )
        if is_platform_admin:
            try:
                room = ChatRoom.objects.get(id=room_id)
                RoomParticipant.objects.get_or_create(
                    room=room,
                    user_id=user_id,
                    defaults={'user_name': getattr(user, 'username', 'Admin'), 'user_role': user_role, 'role': 'ADMIN'}
                )
            except Exception:
                pass
            return True

        is_store_owner = user_role in ['STORE_OWNER', 'SHOP_OWNER', 'TENANT_ADMIN', 'OWNER', 'VENDOR']
        if is_store_owner:
            try:
                room = ChatRoom.objects.get(id=room_id)
                user_tenant_id = getattr(user, 'tenant_id', None)
                if user_tenant_id and room.tenant_id and str(room.tenant_id) == str(user_tenant_id):
                    RoomParticipant.objects.get_or_create(
                        room=room,
                        user_id=user_id,
                        defaults={
                            'user_name': getattr(user, 'username', 'Store Owner'),
                            'user_role': user_role,
                            'role': 'ADMIN'
                        }
                    )
                    return True
            except Exception:
                pass

        return False

    @database_sync_to_async
    def save_message(self, room_id, user, content, media_file_id=None):
        from .models import ChatRoom, ChatMessage, RoomParticipant, MessageRecipientStatus
        from .serializers import ChatMessageSerializer
        try:
            room = ChatRoom.objects.get(id=room_id)
            from .views import ensure_room_participants
            ensure_room_participants(room)
            message_type = 'FILE' if media_file_id else 'TEXT'

            msg = ChatMessage.objects.create(
                room=room,
                sender_id=user.id,
                sender_name=getattr(user, 'username', 'User'),
                sender_role=getattr(user, 'role', 'MEMBER'),
                content=content or '',
                message_type=message_type,
                media_file_id=media_file_id
            )
            room.save()

            sender_display = getattr(user, 'username', 'User')
            preview_text = content[:60] if content else ('[Attachment]' if media_file_id else 'New message')

            from .models import create_recipient_statuses_for_message
            create_recipient_statuses_for_message(msg)

            sender_display = getattr(user, 'username', 'User')
            preview_text = content[:60] if content else ('[Attachment]' if media_file_id else 'New message')

            participants = RoomParticipant.objects.filter(room=room).exclude(user_id=user.id)
            for p in participants:
                try:
                    from .views import send_notification_to_identity
                    send_notification_to_identity(
                        user_id=p.user_id,
                        tenant_id=room.tenant_id,
                        title=f"New message from {sender_display}",
                        message=preview_text,
                        notif_type='CHAT',
                        metadata={
                            'room_id': str(room.id),
                            'message_id': str(msg.id),
                            'sender_name': sender_display,
                            'content': preview_text,
                            'created_at': msg.created_at.isoformat()
                        }
                    )
                except Exception as ex:
                    logger.warning(f"Failed to dispatch chat notification: {ex}")

            try:
                from .views import notify_room_participants_update
                notify_room_participants_update(room, event_type='room_updated', msg=msg)
            except Exception as ex:
                logger.warning(f"Failed to broadcast WS room update: {ex}")

            return ChatMessageSerializer(msg, context={'user_id': user.id}).data
        except Exception as e:
            logger.error(f"Error saving chat message via WebSocket: {e}")
            return None

    @database_sync_to_async
    def get_message_history(self, room_id, before_id=None, limit=20):
        from .models import ChatMessage
        from .serializers import ChatMessageSerializer
        qs = ChatMessage.objects.filter(room_id=room_id, is_deleted=False).order_by('-created_at')
        if before_id:
            try:
                anchor = ChatMessage.objects.get(id=before_id)
                qs = qs.filter(created_at__lt=anchor.created_at)
            except (ChatMessage.DoesNotExist, ValueError, AttributeError, TypeError):
                pass
        total_before = qs.count()
        messages = list(qs[:limit])
        messages.reverse()
        return {
            'room_id': str(room_id),
            'messages': ChatMessageSerializer(messages, many=True, context={'user_id': self.user.id}).data,
            'has_more': total_before > limit
        }

    @database_sync_to_async
    def mark_messages_read(self, room_id, user_id, message_ids=None):
        from .models import update_recipient_statuses_for_user, ChatRoom
        affected_ids = update_recipient_statuses_for_user(room_id, user_id, 'READ', message_ids)
        now = datetime.now(timezone.utc)
        try:
            from .views import notify_room_participants_update
            room = ChatRoom.objects.get(id=room_id)
            notify_room_participants_update(room, event_type='unread_count_update', msg=None)
        except Exception as ex:
            logger.warning(f"Failed to broadcast WS unread count update: {ex}")
        return {
            'room_id': str(room_id),
            'user_id': str(user_id),
            'message_ids': affected_ids,
            'read_at': now.isoformat()
        }

    @database_sync_to_async
    def mark_messages_delivered(self, room_id, user_id, message_ids=None):
        from .models import update_recipient_statuses_for_user
        affected_ids = update_recipient_statuses_for_user(room_id, user_id, 'DELIVERED', message_ids)
        now = datetime.now(timezone.utc)
        return {
            'room_id': str(room_id),
            'user_id': str(user_id),
            'message_ids': affected_ids,
            'delivered_at': now.isoformat()
        }

    @database_sync_to_async
    def toggle_message_reaction(self, message_id, user, emoji):
        from .models import ChatMessage, Reaction
        try:
            msg = ChatMessage.objects.get(id=message_id)
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

            return {
                'message_id': str(message_id),
                'room_id': str(msg.room_id),
                'room': str(msg.room_id),
                'user_id': str(user.id),
                'user_name': getattr(user, 'username', 'User'),
                'emoji': emoji,
                'action': action_type
            }
        except Exception as e:
            logger.error(f"Error toggling message reaction: {e}")
            return None


class UserUpdatesConsumer(AsyncJsonWebsocketConsumer):
    """Global WebSocket stream consumer (/ws/chat/updates/) for presence & session-wide events."""

    async def connect(self):
        self.user = self.scope.get('user')
        self.is_authenticated = False

        await self.accept()

        if self.user and getattr(self.user, 'is_authenticated', False):
            await self._complete_connection(self.user)
        else:
            await self.send_json({
                'type': 'auth_required',
                'data': {'message': 'Authentication required. Send action: "authenticate" with token.'}
            })

    async def _complete_connection(self, user):
        self.user = user
        self.is_authenticated = True
        self.user_id = str(user.id)
        self.user_group = f"user_updates_{self.user_id}"

        await self.channel_layer.group_add(self.user_group, self.channel_name)
        await database_sync_to_async(set_user_online)(user.id)
        await database_sync_to_async(broadcast_presence_event)(user.id, 'online')

        await self.send_json({
            'type': 'connection_established',
            'status': 'authenticated',
            'data': {
                'user_id': self.user_id,
                'message': 'Connected to global updates & presence channel'
            }
        })

    async def disconnect(self, close_code):
        if hasattr(self, 'user_group') and getattr(self, 'is_authenticated', False):
            await database_sync_to_async(set_user_offline)(self.user.id)
            await database_sync_to_async(broadcast_presence_event)(self.user.id, 'offline')
            await self.channel_layer.group_discard(self.user_group, self.channel_name)

    async def receive_json(self, content):
        action = content.get('action') or content.get('type')
        payload = content.get('payload', {})

        if action in ['authenticate', 'auth']:
            token = payload.get('token') or content.get('token')
            from common.ws_auth import decode_jwt_token
            user = decode_jwt_token(token) if token else None

            if not user or not getattr(user, 'is_authenticated', False):
                await self.send_json({'type': 'auth_error', 'message': 'Invalid authentication token.'})
                await self.close(code=4001)
                return

            await self._complete_connection(user)
            return

        if not getattr(self, 'is_authenticated', False) or not self.user:
            await self.send_json({'type': 'error', 'message': 'Unauthorized action. Authenticate first.'})
            return

        if action in ['ping', 'heartbeat']:
            await database_sync_to_async(set_user_online)(self.user.id)
            await self.send_json({'type': 'pong', 'data': {'timestamp': datetime.now(timezone.utc).isoformat()}})

        elif action == 'get_presence':
            target_user_id = payload.get('user_id')
            presence = await database_sync_to_async(get_user_presence)(target_user_id)
            await self.send_json({
                'type': 'presence_info',
                'data': {
                    'user_id': target_user_id,
                    'presence': presence
                }
            })

    async def presence_update(self, event):
        await self.send_json(event)

    async def global_notification(self, event):
        await self.send_json(event)

    async def user_update_event(self, event):
        await self.send_json({
            'type': event.get('event', 'user_update'),
            'data': event.get('data', {})
        })

    async def room_created(self, event):
        await self.send_json({
            'type': 'room_created',
            'data': event.get('data', {})
        })

    async def room_updated(self, event):
        await self.send_json({
            'type': 'room_updated',
            'data': event.get('data', {})
        })

    async def unread_count_update(self, event):
        await self.send_json({
            'type': 'unread_count_update',
            'data': event.get('data', {})
        })

