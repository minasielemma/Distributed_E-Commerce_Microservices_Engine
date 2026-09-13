import uuid
from django.db import models

class Invoice(models.Model):
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('ISSUED', 'Issued'),
        ('PAID', 'Paid'),
        ('OVERDUE', 'Overdue'),
        ('CANCELLED', 'Cancelled'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True, null=True, blank=True)
    customer_id = models.UUIDField(db_index=True, null=True, blank=True)
    order_id = models.UUIDField(db_index=True, null=True, blank=True)
    invoice_number = models.CharField(max_length=100, unique=True, db_index=True)
    billing_period_start = models.DateField(null=True, blank=True)
    billing_period_end = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ISSUED', db_index=True)
    items_summary = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
            models.Index(fields=['customer_id', 'status']),
            models.Index(fields=['customer_id', '-created_at']),
        ]

    def __str__(self):
        return f"Invoice #{self.invoice_number} (${self.total_amount})"
