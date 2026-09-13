import uuid
from django.db import models

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('ORDER', 'Order Update'),
        ('PAYMENT', 'Payment Status'),
        ('SYSTEM', 'System Alert'),
        ('PROMO', 'Promotion'),
        ('SHIPMENT', 'Shipment Status'),
        ('ITEM_REQUEST', 'Product Request'),
        ('CHAT', 'Chat Message'),
        ('CART', 'Cart Event'),
        ('INVENTORY', 'Inventory Alert'),
        ('SECURITY', 'Security Alert'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=100, db_index=True)
    tenant_id = models.CharField(max_length=100, db_index=True, blank=True, null=True)
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES, default='SYSTEM')
    is_read = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id', 'is_read']),
            models.Index(fields=['tenant_id', 'created_at']),
        ]

    def __str__(self):
        return f"Notification ({self.notification_type}) for User {self.user_id}: {self.title}"
