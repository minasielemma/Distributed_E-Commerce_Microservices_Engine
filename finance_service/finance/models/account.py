import uuid
from django.db import models

class Account(models.Model):
    TYPE_CHOICES = (
        ('ASSET', 'Asset'),
        ('LIABILITY', 'Liability'),
        ('EQUITY', 'Equity'),
        ('REVENUE', 'Revenue'),
        ('EXPENSE', 'Expense'),
    )

    BALANCE_CHOICES = (
        ('DEBIT', 'Debit'),
        ('CREDIT', 'Credit'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    account_code = models.CharField(max_length=20, db_index=True)
    account_name = models.CharField(max_length=255)
    account_type = models.CharField(max_length=20, choices=TYPE_CHOICES, db_index=True)
    normal_balance = models.CharField(max_length=10, choices=BALANCE_CHOICES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('tenant_id', 'account_code')
        indexes = [
            models.Index(fields=['tenant_id', 'account_code']),
            models.Index(fields=['tenant_id', 'account_type']),
        ]

    def __str__(self):
        return f"{self.account_code} - {self.account_name} ({self.account_type})"
