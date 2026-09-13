import uuid
from django.db import models

class ItemRequest(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('FULFILLED', 'Fulfilled'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(db_index=True)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    product_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    admin_response = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user_id', 'status']),
            models.Index(fields=['tenant_id', 'status']),
        ]

    def __str__(self):
        return f"ItemRequest {self.product_name} - {self.status}"
