import uuid
from django.db import models
from .tenant import Tenant

class Subscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name='subscription')
    polar_subscription_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    plan_name = models.CharField(max_length=100, default='STARTER')
    status = models.CharField(max_length=50, default='ACTIVE', db_index=True)
    renews_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['polar_subscription_id']),
        ]

    def __str__(self):
        return f"Subscription for {self.tenant.name} - Plan: {self.plan_name}"
