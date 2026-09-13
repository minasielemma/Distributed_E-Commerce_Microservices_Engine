import uuid
from decimal import Decimal
from django.db import models
from django.utils import timezone
from .category import Category

class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    sku = models.CharField(max_length=100, db_index=True)
    polar_product_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)


    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    subcategory = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='subcategory_products')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['tenant_id', 'category']),
            models.Index(fields=['tenant_id', 'subcategory']),
            models.Index(fields=['tenant_id', 'sku']),
            models.Index(fields=['tenant_id', '-created_at']),
        ]

    @property
    def base_price(self):
        if hasattr(self, 'price_detail') and self.price_detail:
            return self.price_detail.base_price
        return Decimal('0.00')

    @property
    def active_discount(self):
        now = timezone.now()
        active_discounts = []
        
        for d in self.discounts.all():
            if d.is_active and d.start_time <= now <= d.end_time:
                active_discounts.append(d)
                
        if self.category:
            for d in self.category.discounts.all():
                if d.is_active and d.start_time <= now <= d.end_time:
                    active_discounts.append(d)
                    
        if not active_discounts:
            return None
            
        active_discounts.sort(key=lambda x: x.priority, reverse=True)
        return active_discounts[0]

    @property
    def dynamic_price(self):
        base = self.base_price
        discount = self.active_discount
        if discount:
            return discount.calculate_discounted_price(base)
        return base

    def __str__(self):
        return f"{self.name} ({self.sku})"
