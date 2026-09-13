import uuid
from decimal import Decimal
from django.db import models
from django.utils import timezone
from .category import Category

class PriceDiscount(models.Model):
    DISCOUNT_TYPE_CHOICES = (
        ('PERCENTAGE', 'Percentage'),
        ('FIXED_AMOUNT', 'Fixed Amount'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='discounts', null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='discounts', null=True, blank=True)
    title = models.CharField(max_length=255)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default='PERCENTAGE')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_active = models.BooleanField(default=True, db_index=True)
    priority = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['tenant_id', 'is_active', 'start_time', 'end_time']),
            models.Index(fields=['product', 'is_active']),
            models.Index(fields=['category', 'is_active']),
        ]

    @property
    def is_currently_valid(self):
        now = timezone.now()
        return self.is_active and (self.start_time <= now <= self.end_time)

    def calculate_discounted_price(self, base_price):
        if not self.is_currently_valid:
            return base_price
        if self.discount_type == 'PERCENTAGE':
            discount_amount = base_price * (self.discount_value / Decimal('100.00'))
            return max(Decimal('0.00'), round(base_price - discount_amount, 2))
        elif self.discount_type == 'FIXED_AMOUNT':
            return max(Decimal('0.00'), round(base_price - self.discount_value, 2))
        return base_price

    def __str__(self):
        return f"{self.title} ({self.discount_type}: {self.discount_value})"
