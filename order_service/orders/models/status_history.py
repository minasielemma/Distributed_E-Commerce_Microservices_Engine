import uuid
from django.db import models

class StatusHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entity_type = models.CharField(max_length=50, db_index=True)  # 'order', 'shipping'
    entity_id = models.UUIDField(db_index=True)
    from_status = models.CharField(max_length=50, blank=True, default='')
    to_status = models.CharField(max_length=50)
    changed_by = models.UUIDField(null=True, blank=True)
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"StatusHistory ({self.entity_type}:{self.entity_id}) {self.from_status} -> {self.to_status}"
