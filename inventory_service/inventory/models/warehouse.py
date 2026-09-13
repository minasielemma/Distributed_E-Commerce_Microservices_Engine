import uuid
from django.db import models

class Warehouse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, db_index=True)
    address = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('tenant_id', 'code')
        indexes = [
            models.Index(fields=['tenant_id', 'code']),
        ]

    def __str__(self):
        return f"Warehouse {self.name} [{self.code}] (Tenant {self.tenant_id})"
