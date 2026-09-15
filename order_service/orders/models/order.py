import uuid
from decimal import Decimal
from django.db import models

class Order(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending Payment'),
        ('PAID', 'Paid / Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('FAILED', 'Failed'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    customer_id = models.UUIDField(db_index=True)
    product_id = models.UUIDField(db_index=True, null=True, blank=True)
    quantity = models.IntegerField(default=1)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_code = models.CharField(max_length=50, blank=True, null=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    polar_checkout_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)

    shipping_address = models.JSONField(default=dict, blank=True)
    billing_address = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
            models.Index(fields=['customer_id', 'status']),
            models.Index(fields=['customer_id', '-created_at']),
        ]

    def can_transition_to(self, target_status):
        from orders.state_machine import OrderStateMachine
        return OrderStateMachine.can_transition(self.status, target_status)

    def transition_to(self, target_status, save=True):
        from orders.state_machine import OrderStateMachine
        return OrderStateMachine.transition(self, target_status, save=save)

    def __str__(self):
        return f"Order {self.id} - Customer {self.customer_id} (${self.total_amount})"

