import uuid
from django.db import models
from .room import ChatRoom


class ChatMessage(models.Model):
    MESSAGE_TYPE_CHOICES = (
        ('TEXT', 'Text'),
        ('FILE', 'File Attachment'),
        ('SYSTEM', 'System Notification'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(ChatRoom, related_name='messages', on_delete=models.CASCADE)
    sender_id = models.UUIDField(db_index=True)
    sender_name = models.CharField(max_length=150, blank=True, default='')
    sender_role = models.CharField(max_length=50, blank=True, default='MEMBER')
    content = models.TextField(blank=True, default='')
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default='TEXT')
    media_file_id = models.UUIDField(null=True, blank=True, db_index=True, help_text="Direct reference ID to MediaFile in media_service")
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'chat'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['room', 'created_at']),
            models.Index(fields=['media_file_id']),
        ]

    def __str__(self):
        return f"ChatMessage {self.id} in Room {self.room_id} by {self.sender_name}"


class MessageRecipientStatus(models.Model):
    STATUS_CHOICES = (
        ('SENT', 'Sent'),
        ('DELIVERED', 'Delivered'),
        ('READ', 'Read'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(ChatMessage, related_name='recipient_statuses', on_delete=models.CASCADE)
    user_id = models.UUIDField(db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SENT')
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'chat'
        unique_together = ('message', 'user_id')
        indexes = [
            models.Index(fields=['user_id', 'status']),
            models.Index(fields=['message', 'status']),
        ]

    def __str__(self):
        return f"Status {self.status} for message {self.message_id} to user {self.user_id}"


class Reaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(ChatMessage, related_name='reactions', on_delete=models.CASCADE)
    user_id = models.UUIDField(db_index=True)
    user_name = models.CharField(max_length=150, blank=True, default='')
    emoji = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('message', 'user_id', 'emoji')
        indexes = [
            models.Index(fields=['message', 'emoji']),
        ]


    def __str__(self):
        return f"Reaction {self.emoji} on message {self.message_id} by {self.user_name}"


def create_recipient_statuses_for_message(message):
    """
    Creates MessageRecipientStatus records with status='SENT' for all non-sender room participants.
    """
    from .room import RoomParticipant
    participants = RoomParticipant.objects.filter(room=message.room).exclude(user_id=message.sender_id)
    to_create = [
        MessageRecipientStatus(message=message, user_id=p.user_id, status='SENT')
        for p in participants
    ]
    if to_create:
        MessageRecipientStatus.objects.bulk_create(to_create, ignore_conflicts=True)


def update_recipient_statuses_for_user(room_id, user_id, target_status, message_ids=None):
    """
    Ensures MessageRecipientStatus objects exist for user_id on all non-sender messages in room_id,
    and updates status to target_status ('DELIVERED' or 'READ').
    Returns a list of string message IDs that were affected/updated.
    """
    from django.utils import timezone
    now = timezone.now()

    msg_qs = ChatMessage.objects.filter(room_id=room_id, is_deleted=False).exclude(sender_id=user_id)
    if message_ids:
        valid_uuids = []
        for val in message_ids:
            try:
                valid_uuids.append(uuid.UUID(str(val)))
            except (ValueError, AttributeError, TypeError):
                pass
        if not valid_uuids:
            return []
        msg_qs = msg_qs.filter(id__in=valid_uuids)

    messages = list(msg_qs)
    if not messages:
        return []

    existing_map = {
        s.message_id: s for s in MessageRecipientStatus.objects.filter(
            message__in=messages,
            user_id=user_id
        )
    }

    affected_msg_ids = []
    to_create = []
    to_update = []

    for msg in messages:
        rec_status = existing_map.get(msg.id)
        if not rec_status:
            to_create.append(MessageRecipientStatus(
                message=msg,
                user_id=user_id,
                status=target_status,
                delivered_at=now if target_status in ['DELIVERED', 'READ'] else None,
                read_at=now if target_status == 'READ' else None
            ))
            affected_msg_ids.append(str(msg.id))
        else:
            should_update = False
            if target_status == 'READ' and rec_status.status != 'READ':
                rec_status.status = 'READ'
                rec_status.read_at = now
                if not rec_status.delivered_at:
                    rec_status.delivered_at = now
                should_update = True
            elif target_status == 'DELIVERED' and rec_status.status == 'SENT':
                rec_status.status = 'DELIVERED'
                rec_status.delivered_at = now
                should_update = True

            if should_update:
                to_update.append(rec_status)
                affected_msg_ids.append(str(msg.id))

    if to_create:
        MessageRecipientStatus.objects.bulk_create(to_create, ignore_conflicts=True)
    if to_update:
        MessageRecipientStatus.objects.bulk_update(to_update, fields=['status', 'delivered_at', 'read_at', 'updated_at'])

    return affected_msg_ids

