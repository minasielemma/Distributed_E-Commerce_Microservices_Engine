import uuid
from django.db import models

class ActivityLog(models.Model):
    STATUS_CHOICES = (
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    actor_id = models.UUIDField(null=True, blank=True, db_index=True)
    actor_email = models.CharField(max_length=255, blank=True, default='')
    actor_role = models.CharField(max_length=50, blank=True, default='')
    action = models.CharField(max_length=100, db_index=True)
    resource_type = models.CharField(max_length=100, blank=True, default='', db_index=True)
    resource_id = models.CharField(max_length=255, blank=True, default='', db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SUCCESS', db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default='')
    details = models.JSONField(default=dict, blank=True)
    changes = models.JSONField(default=dict, blank=True, help_text="Before and after state values")
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['tenant_id', '-timestamp']),
            models.Index(fields=['actor_id', '-timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['action', '-timestamp']),
        ]

    def __str__(self):
        return f"AuditLog {self.action} by {self.actor_email or self.actor_id} at {self.timestamp}"
