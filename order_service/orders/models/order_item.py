import uuid
from decimal import Decimal
from django.db import models

class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, related_name='items')
    suborder = models.ForeignKey('orders.SubOrder', on_delete=models.CASCADE, related_name='items', null=True, blank=True)
    product_id = models.UUIDField(db_index=True)
    variant_id = models.UUIDField(null=True, blank=True, db_index=True)
    product_name = models.CharField(max_length=255, blank=True, default='')
    variant_sku = models.CharField(max_length=100, blank=True, default='')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def total_price(self):
        return (self.unit_price * Decimal(str(self.quantity))).quantize(Decimal('0.01'))

    def __str__(self):
        return f"{self.quantity} x {self.product_name or self.product_id} (${self.total_price})"
