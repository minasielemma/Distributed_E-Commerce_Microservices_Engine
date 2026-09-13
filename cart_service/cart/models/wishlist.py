import uuid
from django.db import models

class Wishlist(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(db_index=True)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    name = models.CharField(max_length=255, default="My Wishlist")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user_id', 'tenant_id']),
        ]

    def __str__(self):
        return f"Wishlist '{self.name}' (User: {self.user_id})"
