import uuid
from django.db import models
from .product import Product

class ProductLike(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(db_index=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user_id', 'product')
        indexes = [
            models.Index(fields=['user_id', 'product']),
        ]

    def __str__(self):
        return f"User {self.user_id} liked {self.product.name}"
