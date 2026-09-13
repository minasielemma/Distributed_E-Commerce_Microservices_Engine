import logging
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from common.ws_auth import decode_jwt_token

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """Consumer for real-time notification push to authenticated clients."""

    async def connect(self):
        self.user = self.scope.get('user')
        self.is_authenticated = False

        await self.accept()

        if self.user and getattr(self.user, 'is_authenticated', False):
            await self._complete_connection(self.user)
        else:
            await self.send_json({
                'type': 'auth_required',
                'message': 'Authentication required. Send action: "authenticate" with token.'
            })

    async def _complete_connection(self, user):
        self.user = user
        self.is_authenticated = True
        self.user_id = str(user.id)
        self.tenant_id = str(getattr(user, 'tenant_id', '')) if getattr(user, 'tenant_id', None) else ''
        self.user_group = f"notifications_{self.user_id}"

        await self.channel_layer.group_add(self.user_group, self.channel_name)

        if self.tenant_id:
            self.tenant_group = f"notifications_tenant_{self.tenant_id}"
            await self.channel_layer.group_add(self.tenant_group, self.channel_name)

        await self.send_json({
            'type': 'connection_established',
            'status': 'authenticated',
            'message': 'Connected to real-time notification service',
            'user_id': self.user_id,
        })

    async def disconnect(self, close_code):
        if hasattr(self, 'user_group') and getattr(self, 'is_authenticated', False):
            await self.channel_layer.group_discard(self.user_group, self.channel_name)
        if hasattr(self, 'tenant_group') and getattr(self, 'is_authenticated', False):
            await self.channel_layer.group_discard(self.tenant_group, self.channel_name)

    async def receive_json(self, content, **kwargs):
        action = content.get('action') or content.get('type')
        payload = content.get('payload', {})

        if action in ['authenticate', 'auth']:
            token = payload.get('token') or content.get('token')
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
            await self.send_json({'type': 'pong'})

    async def notification_message(self, event):
        """Handler for 'notification_message' or 'notification.message' group events from Channel Layer."""
        await self.send_json({
            'type': 'notification',
            'data': event.get('data', {}),
        })

    async def notification_send(self, event):
        """Handler for 'notification_send' group events."""
        await self.send_json({
            'type': 'notification',
            'data': event.get('data', {}),
        })
