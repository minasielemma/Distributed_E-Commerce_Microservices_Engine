import uuid
from django.db import models
from .inventory_item import InventoryItem

class StockMovement(models.Model):
    MOVEMENT_TYPES = (
        ('INBOUND', 'Inbound Restock'),
        ('OUTBOUND', 'Outbound Fulfillment'),
        ('RESERVED', 'Reserved for Order'),
        ('RELEASED', 'Released Reservation'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES, db_index=True)
    quantity = models.IntegerField()
    reference_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['inventory_item', '-created_at']),
            models.Index(fields=['tenant_id', 'reference_id']),
        ]

    def __str__(self):
        return f"Movement {self.movement_type} ({self.quantity}) for Item {self.inventory_item.id}"
