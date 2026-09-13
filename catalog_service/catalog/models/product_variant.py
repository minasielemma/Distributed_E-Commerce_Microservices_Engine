import uuid
from decimal import Decimal
from django.db import models
from .product import Product
from .product_attribute import ProductAttributeValue

class ProductVariant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    sku = models.CharField(max_length=100, unique=True, db_index=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    attribute_values = models.ManyToManyField(ProductAttributeValue, related_name='variants', blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['tenant_id', 'product']),
            models.Index(fields=['sku']),
        ]

    @property
    def effective_price(self):
        if self.price is not None:
            return Decimal(str(self.price))
        return self.product.dynamic_price

    def __str__(self):
        return f"{self.product.name} - Variant ({self.sku})"
