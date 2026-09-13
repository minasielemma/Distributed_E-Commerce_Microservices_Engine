import uuid
from decimal import Decimal
from django.db import models

class ProductPrice(models.Model):
    CURRENCY_CHOICES = (
        ('USD', 'USD - US Dollar'),
        ('EUR', 'EUR - Euro'),
        ('GBP', 'GBP - British Pound'),
        ('JPY', 'JPY - Japanese Yen'),
        ('CAD', 'CAD - Canadian Dollar'),
        ('AUD', 'AUD - Australian Dollar'),
        ('AED', 'AED - UAE Dirham'),
        ('SAR', 'SAR - Saudi Riyal'),
        ('ETB', 'ETB - Ethiopian Birr'),
        ('KES', 'KES - Kenyan Shilling'),
        ('INR', 'INR - Indian Rupee'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.OneToOneField('Product', on_delete=models.CASCADE, related_name='price_detail')
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['tenant_id', 'currency']),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.currency} {self.base_price}"
