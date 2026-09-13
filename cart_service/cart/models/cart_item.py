import uuid
from django.db import models
from .cart import Cart

class CartItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product_id = models.UUIDField(db_index=True)
    variant_id = models.UUIDField(null=True, blank=True, db_index=True)
    variant_name = models.CharField(max_length=255, blank=True, default='')
    product_name = models.CharField(max_length=255, blank=True, default='')
    image_url = models.CharField(max_length=500, blank=True, default='')
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['cart', 'product_id']),
        ]

    def __str__(self):
        return f"CartItem {self.product_id} x{self.quantity}"
