import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from .product import Product

class ProductReview(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user_id = models.UUIDField(null=True, blank=True, db_index=True)
    user_name = models.CharField(max_length=150, blank=True, default='')
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=150, blank=True, null=True)
    review_text = models.TextField()
    is_verified_purchase = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['product', 'user_id']

    def __str__(self):
        return f"Review ({self.rating} stars) for {self.product.name}"
