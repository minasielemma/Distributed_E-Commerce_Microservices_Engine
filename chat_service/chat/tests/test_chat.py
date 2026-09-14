import uuid
from unittest.mock import patch
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from chat.models import ChatRoom, RoomParticipant
from common.ws_auth import GatewayUser


class MockGatewayUser(GatewayUser):
    def __init__(self, user_id, role='CUSTOMER', permissions=None, is_platform_admin=False):
        self.id = user_id
        self.pk = user_id
        self.username = f"user_{str(user_id)[:6]}"
        self.email = f"{self.username}@example.com"
        self.role = role
        self.permissions = permissions or []
        self.is_authenticated = True
        self.is_anonymous = False
        self.is_platform_admin = is_platform_admin
        self.is_staff = is_platform_admin
        self.is_superuser = is_platform_admin

    def has_perm(self, perm):
        return perm in self.permissions


class ChatRoomParticipantRemovalTests(TestCase):
    def setUp(self):
        self.owner_id = uuid.uuid4()
        self.admin_member_id = uuid.uuid4()
        self.regular_member_id = uuid.uuid4()
        self.target_user_id = uuid.uuid4()
        self.platform_admin_id = uuid.uuid4()
        self.permitted_user_id = uuid.uuid4()

        self.room = ChatRoom.objects.create(
            name="Test Chat Room",
            room_type="GROUP",
            created_by=self.owner_id
        )

        # Room owner participant
        RoomParticipant.objects.create(
            room=self.room,
            user_id=self.owner_id,
            user_name="Owner User",
            role="OWNER"
        )
        # Room admin participant
        RoomParticipant.objects.create(
            room=self.room,
            user_id=self.admin_member_id,
            user_name="Admin User",
            role="ADMIN"
        )
        # Regular member participant
        RoomParticipant.objects.create(
            room=self.room,
            user_id=self.regular_member_id,
            user_name="Regular Member",
            role="MEMBER"
        )
        # Target participant to be removed
        RoomParticipant.objects.create(
            room=self.room,
            user_id=self.target_user_id,
            user_name="Target Member",
            role="MEMBER"
        )

    def test_owner_can_remove_participant(self):
        client = APIClient()
        owner_user = MockGatewayUser(self.owner_id)
        client.force_authenticate(user=owner_user)

        url = f"/api/chat/rooms/{self.room.id}/participants/{self.target_user_id}/"
        response = client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(RoomParticipant.objects.filter(room=self.room, user_id=self.target_user_id).exists())

    def test_room_admin_can_remove_participant(self):
        client = APIClient()
        admin_user = MockGatewayUser(self.admin_member_id)
        client.force_authenticate(user=admin_user)

        url = f"/api/chat/rooms/{self.room.id}/participants/{self.target_user_id}/"
        response = client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(RoomParticipant.objects.filter(room=self.room, user_id=self.target_user_id).exists())

    def test_regular_member_cannot_remove_another_participant(self):
        client = APIClient()
        regular_user = MockGatewayUser(self.regular_member_id)
        client.force_authenticate(user=regular_user)

        url = f"/api/chat/rooms/{self.room.id}/participants/{self.target_user_id}/"
        response = client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(RoomParticipant.objects.filter(room=self.room, user_id=self.target_user_id).exists())

    def test_regular_member_can_remove_themselves(self):
        client = APIClient()
        regular_user = MockGatewayUser(self.regular_member_id)
        client.force_authenticate(user=regular_user)

        url = f"/api/chat/rooms/{self.room.id}/participants/{self.regular_member_id}/"
        response = client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(RoomParticipant.objects.filter(room=self.room, user_id=self.regular_member_id).exists())

    def test_platform_admin_can_remove_participant(self):
        client = APIClient()
        admin_user = MockGatewayUser(self.platform_admin_id, role='PLATFORM_ADMIN', is_platform_admin=True)
        client.force_authenticate(user=admin_user)

        url = f"/api/chat/rooms/{self.room.id}/participants/{self.target_user_id}/"
        response = client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(RoomParticipant.objects.filter(room=self.room, user_id=self.target_user_id).exists())

    def test_permitted_user_can_remove_participant(self):
        # Add permitted user as a participant so room is accessible in get_queryset
        RoomParticipant.objects.create(
            room=self.room,
            user_id=self.permitted_user_id,
            user_name="Permitted User",
            role="MEMBER"
        )
        client = APIClient()
        permitted_user = MockGatewayUser(self.permitted_user_id, permissions=['chat.remove_participant'])
        client.force_authenticate(user=permitted_user)

        url = f"/api/chat/rooms/{self.room.id}/participants/{self.target_user_id}/"
        response = client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(RoomParticipant.objects.filter(room=self.room, user_id=self.target_user_id).exists())

    def test_regular_member_cannot_add_participant(self):
        client = APIClient()
        regular_user = MockGatewayUser(self.regular_member_id)
        client.force_authenticate(user=regular_user)

        new_user_id = uuid.uuid4()
        url = f"/api/chat/rooms/{self.room.id}/participants/"
        response = client.post(url, {'user_id': str(new_user_id), 'user_name': 'New User'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_can_add_participant(self):
        client = APIClient()
        owner_user = MockGatewayUser(self.owner_id)
        client.force_authenticate(user=owner_user)

        new_user_id = uuid.uuid4()
        url = f"/api/chat/rooms/{self.room.id}/participants/"
        response = client.post(url, {'user_id': str(new_user_id), 'user_name': 'New User'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(RoomParticipant.objects.filter(room=self.room, user_id=new_user_id).exists())

    def test_direct_room_participant_limit(self):
        direct_room = ChatRoom.objects.create(name="Direct Chat", room_type="DIRECT", created_by=self.owner_id)
        u1 = uuid.uuid4()
        u2 = uuid.uuid4()
        u3 = uuid.uuid4()
        RoomParticipant.objects.create(room=direct_room, user_id=u1, user_name="User 1", role="OWNER")
        RoomParticipant.objects.create(room=direct_room, user_id=u2, user_name="User 2", role="MEMBER")

        client = APIClient()
        owner_user = MockGatewayUser(u1)
        client.force_authenticate(user=owner_user)

        url = f"/api/chat/rooms/{direct_room.id}/participants/"
        response = client.post(url, {'user_id': str(u3), 'user_name': 'User 3'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_participant_cannot_access_room_messages(self):
        non_participant_id = uuid.uuid4()
        client = APIClient()
        outsider = MockGatewayUser(non_participant_id)
        client.force_authenticate(user=outsider)

        # GET messages -> 404 (because get_queryset filters rooms to own participant rooms)
        url = f"/api/chat/rooms/{self.room.id}/messages/"
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AutoAddParticipantsTests(TestCase):
    def setUp(self):
        self.creator_id = uuid.uuid4()
        self.store_owner_id = uuid.uuid4()
        self.admin_id = uuid.uuid4()
        self.tenant_id = uuid.uuid4()
        self.order_id = uuid.uuid4()

    @patch('requests.get')
    def test_auto_add_store_owner_with_tenant_id(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'results': [
                {'id': str(self.store_owner_id), 'username': 'shop_owner_1', 'role': 'STORE_OWNER'}
            ]
        }

        client = APIClient()
        user = MockGatewayUser(self.creator_id)
        client.force_authenticate(user=user)

        response = client.post('/api/chat/rooms/', {
            'name': 'Order Discussion',
            'tenant_id': str(self.tenant_id),
            'room_type': 'ORDER_SUPPORT'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        room_id = response.data['id']
        self.assertTrue(RoomParticipant.objects.filter(room_id=room_id, user_id=self.store_owner_id).exists())

    @patch('requests.get')
    def test_auto_add_store_owner_with_order_id(self, mock_get):
        def side_effect(url, **kwargs):
            class MockResponse:
                def __init__(self, status_code, data):
                    self.status_code = status_code
                    self._data = data
                    self.text = ""
                def json(self):
                    return self._data

            if 'order_service' in url or '/api/orders/' in url:
                return MockResponse(200, {'id': str(self.order_id), 'tenant_id': str(self.tenant_id)})
            if 'identity_service' in url or '/lookup/' in url:
                return MockResponse(200, {
                    'results': [{'id': str(self.store_owner_id), 'username': 'shop_owner_1', 'role': 'STORE_OWNER'}]
                })
            return MockResponse(404, {})

        mock_get.side_effect = side_effect

        client = APIClient()
        user = MockGatewayUser(self.creator_id)
        client.force_authenticate(user=user)

        response = client.post('/api/chat/rooms/', {
            'name': 'Chat for Order',
            'order_id': str(self.order_id)
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        room_id = response.data['id']
        self.assertTrue(RoomParticipant.objects.filter(room_id=room_id, user_id=self.store_owner_id).exists())

    @patch('chat.views.broadcast_room_ws')
    def test_send_message_broadcasts_new_message_event(self, mock_broadcast):
        user_id = uuid.uuid4()
        room = ChatRoom.objects.create(name="Message Test Room", created_by=user_id)
        RoomParticipant.objects.create(room=room, user_id=user_id, user_name="Test User", role="MEMBER")

        client = APIClient()
        user = MockGatewayUser(user_id)
        client.force_authenticate(user=user)

        response = client.post(f'/api/chat/rooms/{room.id}/messages/', {'content': 'Hello world'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_broadcast.assert_called_once()
        args = mock_broadcast.call_args[0]
        self.assertEqual(args[0], room.id)
        self.assertEqual(args[1], 'new_message_event')


class ChatRoomMessageIsolationTests(TestCase):
    def test_serializer_outputs_room_and_room_id(self):
        from chat.models import ChatMessage
        from chat.serializers import ChatMessageSerializer

        user_id = uuid.uuid4()
        room = ChatRoom.objects.create(name="Room A", created_by=user_id)
        msg = ChatMessage.objects.create(room=room, sender_id=user_id, sender_name="Tester", content="Isolated message")

        serializer_data = ChatMessageSerializer(msg).data
        self.assertIn('room', serializer_data)
        self.assertIn('room_id', serializer_data)
        self.assertEqual(serializer_data['room'], str(room.id))
        self.assertEqual(serializer_data['room_id'], str(room.id))

    @patch('chat.views.get_channel_layer')
    def test_broadcast_room_ws_attaches_room_id(self, mock_get_channel_layer):
        from chat.views import broadcast_room_ws
        from unittest.mock import AsyncMock, MagicMock

        mock_layer = MagicMock()
        mock_layer.group_send = AsyncMock()
        mock_get_channel_layer.return_value = mock_layer

        room_id = uuid.uuid4()
        msg_data = {'id': 'msg-123', 'content': 'Test broadcast'}

        broadcast_room_ws(room_id, 'new_message_event', msg_data)

        self.assertEqual(msg_data.get('room_id'), str(room_id))
        self.assertEqual(msg_data.get('room'), str(room_id))

    @patch('chat.views.get_channel_layer')
    def test_notify_room_participants_update_broadcasts_events(self, mock_get_channel_layer):
        from chat.views import notify_room_participants_update
        from unittest.mock import AsyncMock, MagicMock

        mock_layer = MagicMock()
        mock_layer.group_send = AsyncMock()
        mock_get_channel_layer.return_value = mock_layer

        u1 = uuid.uuid4()
        u2 = uuid.uuid4()
        room = ChatRoom.objects.create(name="Room Broadcast Test", created_by=u1)
        RoomParticipant.objects.create(room=room, user_id=u1, user_name="User 1", role="OWNER")
        RoomParticipant.objects.create(room=room, user_id=u2, user_name="User 2", role="MEMBER")

        notify_room_participants_update(room, event_type='room_created')

        self.assertEqual(mock_layer.group_send.call_count, 2)
        group_names = [call[0][0] for call in mock_layer.group_send.call_args_list]
        self.assertIn(f"user_updates_{u1}", group_names)
        self.assertIn(f"user_updates_{u2}", group_names)
