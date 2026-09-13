import uuid
from django.db import models


class Conversation(models.Model):
    STATUS_CHOICES = (
        ('OPEN', 'Open'),
        ('CLOSED', 'Closed'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    customer_id = models.UUIDField(db_index=True)
    customer_name = models.CharField(max_length=150, blank=True, default='')
    order_id = models.UUIDField(null=True, blank=True, db_index=True)
    subject = models.CharField(max_length=255, default='Order Inquiry')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    last_message_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-last_message_at']
        indexes = [
            models.Index(fields=['tenant_id', 'customer_id']),
            models.Index(fields=['tenant_id', 'status']),
        ]

    def __str__(self):
        return f"Conversation {self.id} - Customer {self.customer_id} (Tenant {self.tenant_id})"


class Message(models.Model):
    SENDER_TYPE_CHOICES = (
        ('CUSTOMER', 'Customer'),
        ('SHOP_OWNER', 'Shop Owner'),
        ('SYSTEM', 'System'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, related_name='messages', on_delete=models.CASCADE)
    sender_id = models.UUIDField()
    sender_type = models.CharField(max_length=20, choices=SENDER_TYPE_CHOICES)
    sender_name = models.CharField(max_length=150, blank=True, default='')
    content = models.TextField()
    is_read_by_customer = models.BooleanField(default=False)
    is_read_by_owner = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message {self.id} by {self.sender_type} ({self.sender_name})"
