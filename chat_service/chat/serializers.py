from rest_framework import serializers
from .models import ChatRoom, RoomParticipant, ChatMessage, MessageRecipientStatus, Reaction


class RoomParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomParticipant
        fields = ['id', 'room', 'user_id', 'user_name', 'user_role', 'role', 'joined_at']
        read_only_fields = ['id', 'room', 'joined_at']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        for k in ['id', 'room', 'user_id']:
            if k in ret and ret[k] is not None:
                ret[k] = str(ret[k])
        return ret


class ReactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reaction
        fields = ['id', 'message', 'user_id', 'user_name', 'emoji', 'created_at']
        read_only_fields = ['id', 'message', 'created_at']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        for k in ['id', 'message', 'user_id']:
            if k in ret and ret[k] is not None:
                ret[k] = str(ret[k])
        return ret


class MessageRecipientStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageRecipientStatus
        fields = ['id', 'message', 'user_id', 'status', 'delivered_at', 'read_at', 'updated_at']
        read_only_fields = ['id', 'message', 'updated_at']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        for k in ['id', 'message', 'user_id']:
            if k in ret and ret[k] is not None:
                ret[k] = str(ret[k])
        return ret


class ChatMessageSerializer(serializers.ModelSerializer):
    room_id = serializers.CharField(read_only=True)
    attachment_download_url = serializers.SerializerMethodField()
    reactions = serializers.SerializerMethodField()
    recipient_status = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = [
            'id', 'room', 'room_id', 'sender_id', 'sender_name', 'sender_role',
            'content', 'message_type', 'media_file_id', 'attachment_download_url',
            'is_edited', 'is_deleted', 'reactions', 'recipient_status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'room', 'room_id', 'sender_id', 'sender_name', 'created_at', 'updated_at', 'attachment_download_url']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        for k in ['id', 'room', 'room_id', 'sender_id', 'media_file_id']:
            if k in ret and ret[k] is not None:
                ret[k] = str(ret[k])
        if ret.get('room') and not ret.get('room_id'):
            ret['room_id'] = ret['room']
        return ret

    def get_attachment_download_url(self, obj):
        if obj.media_file_id:
            return f"/api/chat/rooms/{obj.room_id}/files/{obj.media_file_id}/download/"
        return None

    def get_reactions(self, obj):
        reactions_qs = obj.reactions.all()
        aggregated = {}
        for r in reactions_qs:
            if r.emoji not in aggregated:
                aggregated[r.emoji] = {'emoji': r.emoji, 'count': 0, 'users': []}
            aggregated[r.emoji]['count'] += 1
            aggregated[r.emoji]['users'].append({'user_id': str(r.user_id), 'user_name': r.user_name})
        return list(aggregated.values())

    def get_recipient_status(self, obj):
        user_id = None
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user_id = getattr(request.user, 'id', None)
        if not user_id:
            user_id = self.context.get('user_id')
        if not user_id:
            return 'SENT'

        user_id_str = str(user_id)
        if str(obj.sender_id) == user_id_str:
            statuses = [s.status for s in obj.recipient_statuses.all()]
            if 'READ' in statuses:
                return 'READ'
            if 'DELIVERED' in statuses:
                return 'DELIVERED'
            return 'SENT'
        else:
            rec_statuses = [s for s in obj.recipient_statuses.all() if str(s.user_id) == user_id_str]
            return rec_statuses[0].status if rec_statuses else 'SENT'


class ChatRoomSerializer(serializers.ModelSerializer):
    participants = RoomParticipantSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = [
            'id', 'tenant_id', 'name', 'room_type', 'order_id',
            'created_by', 'is_active', 'last_message_at', 'created_at',
            'participants', 'last_message', 'unread_count'
        ]
        read_only_fields = ['id', 'created_by', 'last_message_at', 'created_at']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        for k in ['id', 'tenant_id', 'order_id', 'created_by']:
            if k in ret and ret[k] is not None:
                ret[k] = str(ret[k])
        return ret

    def get_last_message(self, obj):
        last_msg = obj.messages.filter(is_deleted=False).order_by('-created_at').first()
        if last_msg:
            return ChatMessageSerializer(last_msg, context=self.context).data
        return None

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if not request or not hasattr(request, 'user'):
            return 0
        user_id = getattr(request.user, 'id', None)
        if not user_id:
            return 0
        return ChatMessage.objects.filter(
            room=obj
        ).exclude(
            sender_id=user_id
        ).exclude(
            recipient_statuses__user_id=user_id,
            recipient_statuses__status='READ'
        ).count()


class ChatRoomDetailSerializer(ChatRoomSerializer):
    messages = serializers.SerializerMethodField()

    class Meta(ChatRoomSerializer.Meta):
        fields = ChatRoomSerializer.Meta.fields + ['messages']

    def get_messages(self, obj):
        messages_qs = obj.messages.filter(is_deleted=False).prefetch_related('recipient_statuses', 'reactions').order_by('-created_at')[:50]
        messages_list = list(messages_qs)
        messages_list.reverse()
        return ChatMessageSerializer(messages_list, many=True, context=self.context).data


class CreateChatRoomSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, default='Chat Room')
    room_type = serializers.ChoiceField(choices=ChatRoom.ROOM_TYPE_CHOICES, default='DIRECT')
    tenant_id = serializers.UUIDField(required=False, allow_null=True)
    order_id = serializers.UUIDField(required=False, allow_null=True)
    participant_user_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, default=list
    )
    initial_message = serializers.CharField(required=False, allow_blank=True, default='')


class AddParticipantSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, required=False, allow_blank=True, default='')
    user_id = serializers.CharField(max_length=150, required=False, allow_blank=True, default='')
    user_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default='')
    user_role = serializers.CharField(max_length=50, required=False, allow_blank=True, default='MEMBER')
    role = serializers.ChoiceField(choices=RoomParticipant.ROLE_CHOICES, default='MEMBER')

    def validate(self, attrs):
        if not attrs.get('username') and not attrs.get('user_id'):
            raise serializers.ValidationError('Either username or user_id is required.')
        return attrs


class SendMessageSerializer(serializers.Serializer):
    content = serializers.CharField(required=False, allow_blank=True, default='')
    media_file_id = serializers.UUIDField(required=False, allow_null=True)

    def validate(self, attrs):
        if not attrs.get('content') and not attrs.get('media_file_id'):
            raise serializers.ValidationError('Either message content or media_file_id attachment must be provided.')
        return attrs
