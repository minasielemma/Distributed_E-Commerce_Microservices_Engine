import uuid
from django.db import models
from .warehouse import Warehouse

class InventoryItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    product_id = models.UUIDField(db_index=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='items')
    quantity_available = models.IntegerField(default=0)
    quantity_reserved = models.IntegerField(default=0)
    reorder_level = models.IntegerField(default=10)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant_id', 'product_id', 'warehouse')
        indexes = [
            models.Index(fields=['tenant_id', 'product_id']),
            models.Index(fields=['tenant_id', 'warehouse']),
        ]

    def __str__(self):
        return f"Stock Product {self.product_id}: {self.quantity_available} avail ({self.quantity_reserved} res)"
