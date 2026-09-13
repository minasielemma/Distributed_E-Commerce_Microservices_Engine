from rest_framework import serializers
from .models.chat import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = [
            'id',
            'conversation',
            'sender_id',
            'sender_type',
            'sender_name',
            'content',
            'is_read_by_customer',
            'is_read_by_owner',
            'created_at',
        ]
        read_only_fields = ['id', 'conversation', 'sender_id', 'sender_type', 'sender_name', 'created_at']


class ConversationSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'id',
            'tenant_id',
            'customer_id',
            'customer_name',
            'order_id',
            'subject',
            'status',
            'last_message_at',
            'created_at',
            'last_message',
            'unread_count',
        ]
        read_only_fields = ['id', 'tenant_id', 'customer_id', 'last_message_at', 'created_at']

    def get_last_message(self, obj):
        last_msg = obj.messages.order_by('-created_at').first()
        if last_msg:
            return MessageSerializer(last_msg).data
        return None

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if not request or not hasattr(request, 'user'):
            return 0
        user = request.user
        # If customer, count unread where is_read_by_customer=False and sender_type != 'CUSTOMER'
        if getattr(user, 'role', '') == 'CUSTOMER' or str(user.id) == str(obj.customer_id):
            return obj.messages.filter(is_read_by_customer=False).exclude(sender_type='CUSTOMER').count()
        else:
            return obj.messages.filter(is_read_by_owner=False).exclude(sender_type='SHOP_OWNER').count()


class ConversationDetailSerializer(ConversationSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta(ConversationSerializer.Meta):
        fields = ConversationSerializer.Meta.fields + ['messages']


class CreateConversationSerializer(serializers.Serializer):
    order_id = serializers.UUIDField(required=False, allow_null=True)
    subject = serializers.CharField(max_length=255, default='Order Inquiry')
    initial_message = serializers.CharField()
