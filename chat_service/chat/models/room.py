import uuid
from django.db import models


class ChatRoom(models.Model):
    ROOM_TYPE_CHOICES = (
        ('DIRECT', 'Direct 1-on-1'),
        ('GROUP', 'Group Chat'),
        ('ORDER_SUPPORT', 'Order Support'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    name = models.CharField(max_length=255, default='Chat Room')
    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES, default='DIRECT')
    order_id = models.UUIDField(null=True, blank=True, db_index=True)
    created_by = models.UUIDField(db_index=True)
    is_active = models.BooleanField(default=True)
    last_message_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'chat'
        ordering = ['-last_message_at']
        indexes = [
            models.Index(fields=['tenant_id', 'room_type']),
            models.Index(fields=['created_by']),
        ]



    def __str__(self):
        return f"ChatRoom '{self.name}' ({self.id})"


class RoomParticipant(models.Model):
    ROLE_CHOICES = (
        ('OWNER', 'Owner'),
        ('ADMIN', 'Admin'),
        ('MEMBER', 'Member'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(ChatRoom, related_name='participants', on_delete=models.CASCADE)
    user_id = models.UUIDField(db_index=True)
    user_name = models.CharField(max_length=150, blank=True, default='')
    user_role = models.CharField(max_length=50, blank=True, default='CUSTOMER')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='MEMBER')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'chat'
        unique_together = ('room', 'user_id')
        indexes = [
            models.Index(fields=['user_id', 'room']),
        ]



    def __str__(self):
        return f"Participant {self.user_name} in {self.room_id}"
