import uuid
from django.db import models
from .user import User

class Tenant(models.Model):
    TIER_CHOICES = (
        ('STARTER', 'Starter Tier'),
        ('GROWTH', 'Growth Tier'),
        ('ENTERPRISE', 'Enterprise Tier'),
    )

    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('SUSPENDED', 'Suspended'),
        ('CANCELLED', 'Cancelled'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    domain = models.CharField(max_length=255, unique=True, db_index=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tenants')
    subscription_tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='STARTER')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE', db_index=True)

    has_catalog_access = models.BooleanField(default=True)
    has_inventory_access = models.BooleanField(default=True)
    has_finance_access = models.BooleanField(default=True)
    has_payment_access = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['domain', 'status']),
            models.Index(fields=['owner', 'status']),
        ]

    def __str__(self):
        return f"Shop {self.name} [{self.domain}] - Tier: {self.subscription_tier}"
