import uuid
from django.db import models

class JournalEntry(models.Model):
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('POSTED', 'Posted'),
        ('REVERSED', 'Reversed'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    entry_number = models.CharField(max_length=50, unique=True, db_index=True)
    date = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, default="")
    reference_id = models.CharField(max_length=255, blank=True, default="", db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='POSTED', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['tenant_id', '-created_at']),
            models.Index(fields=['tenant_id', 'reference_id']),
        ]

    def __str__(self):
        return f"Journal Entry #{self.entry_number} [{self.status}]"
