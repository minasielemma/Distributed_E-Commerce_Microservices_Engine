import uuid
from django.db import models

class Cart(models.Model):
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('CHECKED_OUT', 'Checked Out'),
        ('ABANDONED', 'Abandoned'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(db_index=True)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE', db_index=True)
    coupon_code = models.CharField(max_length=50, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user_id', 'status']),
            models.Index(fields=['tenant_id', 'status']),
        ]

    def subtotal(self):
        from decimal import Decimal
        return sum((item.quantity * item.price for item in self.items.all()), Decimal('0.00'))

    def total(self):
        from decimal import Decimal
        sub = self.subtotal()
        disc = Decimal(str(self.discount_amount or '0.00'))
        return max(Decimal('0.00'), sub - disc)


    def __str__(self):
        return f"Cart {self.id} (User: {self.user_id})"

