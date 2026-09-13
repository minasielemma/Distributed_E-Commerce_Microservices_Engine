import uuid
from django.db import models
from .wishlist import Wishlist

class WishlistItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items')
    product_id = models.UUIDField(db_index=True)
    product_name = models.CharField(max_length=255, blank=True, default="")
    image_url = models.TextField(blank=True, default="")
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    note = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['wishlist', 'product_id']),
        ]

    def __str__(self):
        return f"WishlistItem {self.product_name or self.product_id}"
