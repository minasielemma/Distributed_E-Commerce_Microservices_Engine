import uuid
from django.db import models

class TenantLedger(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(unique=True, db_index=True)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    platform_fees_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    available_payout_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=10, default='USD')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['tenant_id']),
        ]

    def __str__(self):
        return f"Ledger Tenant {self.tenant_id} - Avail Balance: ${self.available_payout_balance}"
