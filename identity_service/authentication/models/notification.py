import uuid
from django.db import models
from django.conf import settings

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('ORDER', 'Order Update'),
        ('PAYMENT', 'Payment Status'),
        ('SYSTEM', 'System Alert'),
        ('PROMO', 'Promotion'),
        ('SHIPMENT', 'Shipment Status'),
        ('ITEM_REQUEST', 'Product Request'),
        ('CHAT', 'Chat Message'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='SYSTEM')
    is_read = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self):
        return f"Notification ({self.notification_type}) for {self.user.username}: {self.title}"
