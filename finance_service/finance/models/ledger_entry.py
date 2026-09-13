import uuid
from django.db import models
from .tenant_ledger import TenantLedger

class LedgerEntry(models.Model):
    ENTRY_TYPES = (
        ('CREDIT_SALE', 'Gross Sale Revenue Credit'),
        ('DEBIT_PLATFORM_FEE', 'SaaS Platform Fee Debit'),
        ('DEBIT_PAYOUT', 'Shop Payout Debit'),
        ('CREDIT_REFUND', 'Order Refund Adjustment'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    ledger = models.ForeignKey(TenantLedger, on_delete=models.CASCADE, related_name='entries')
    entry_type = models.CharField(max_length=30, choices=ENTRY_TYPES, db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    reference_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant_id', '-created_at']),
            models.Index(fields=['ledger', '-created_at']),
        ]

    def __str__(self):
        return f"Entry [{self.entry_type}] ${self.amount} for Tenant {self.tenant_id}"
