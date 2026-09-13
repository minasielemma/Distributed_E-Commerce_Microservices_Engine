import uuid
from django.db import models

class UserInteraction(models.Model):
    INTERACTION_TYPES = [
        ('VIEW', 'View'),
        ('LIKE', 'Like'),
        ('WISHLIST', 'Wishlist'),
        ('CART', 'Cart'),
        ('PURCHASE', 'Purchase'),
        ('REVIEW', 'Review'),
    ]

    event_id = models.CharField(max_length=255, unique=True, null=True, blank=True, db_index=True)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    user_id = models.UUIDField(db_index=True)
    product_id = models.UUIDField(db_index=True)
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES, db_index=True)
    weight = models.FloatField(default=1.0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['user_id', 'interaction_type']),
            models.Index(fields=['tenant_id', 'product_id']),
            models.Index(fields=['tenant_id', 'user_id']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user_id} - {self.interaction_type} - {self.product_id}"


class ProductMetadataCache(models.Model):
    product_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    category_id = models.UUIDField(null=True, blank=True, db_index=True)
    category_name = models.CharField(max_length=255, blank=True, default='')
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    rating_avg = models.FloatField(default=0.0)
    purchase_count = models.IntegerField(default=0)
    view_count = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['tenant_id', 'category_id']),
            models.Index(fields=['tenant_id', '-purchase_count']),
        ]

    def __str__(self):
        return f"{self.name} ({self.product_id})"


class CachedRecommendation(models.Model):
    RECOMMENDATION_TYPES = [
        ('PERSONALIZED', 'Personalized'),
        ('SIMILAR', 'Similar Products'),
        ('CO_PURCHASE', 'Frequently Bought Together'),
        ('TRENDING', 'Trending Products'),
    ]

    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    user_id = models.UUIDField(null=True, blank=True, db_index=True)
    recommendation_type = models.CharField(max_length=30, choices=RECOMMENDATION_TYPES, db_index=True)
    source_product_id = models.UUIDField(null=True, blank=True, db_index=True)
    recommendations_json = models.JSONField(default=list)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['user_id', 'recommendation_type']),
            models.Index(fields=['source_product_id', 'recommendation_type']),
            models.Index(fields=['tenant_id', 'recommendation_type']),
        ]
        unique_together = [
            ('tenant_id', 'user_id', 'recommendation_type', 'source_product_id')
        ]

    def __str__(self):
        return f"{self.recommendation_type} - User:{self.user_id} Prod:{self.source_product_id}"
