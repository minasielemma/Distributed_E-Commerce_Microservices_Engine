import uuid
from django.db import models

class MediaFile(models.Model):
    FILE_TYPES = [
        ('IMAGE', 'Image'),
        ('DOCUMENT', 'Document'),
        ('OTHER', 'Other'),
    ]

    VISIBILITY_CHOICES = [
        ('PUBLIC', 'Public'),
        ('PRIVATE', 'Private'),
        ('SHARED', 'Shared'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    uploaded_by = models.CharField(max_length=255, db_index=True, null=True, blank=True)
    original_filename = models.CharField(max_length=255)
    file_url = models.URLField(max_length=500)
    storage_path = models.CharField(max_length=500)
    content_type = models.CharField(max_length=100)
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    file_type = models.CharField(max_length=20, choices=FILE_TYPES, default='IMAGE')
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='PUBLIC', db_index=True)
    shared_with_users = models.JSONField(default=list, blank=True, help_text="List of user UUID/ID strings granted access")
    shared_with_tenants = models.JSONField(default=list, blank=True, help_text="List of tenant UUID strings granted access")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant_id', 'created_at']),
            models.Index(fields=['uploaded_by', 'visibility']),
        ]

    def has_access(self, user):
        if self.visibility == 'PUBLIC':
            return True
        if not user or not user.is_authenticated:
            return False

        user_id_str = str(user.id)
        role = getattr(user, 'role', '').upper()
        if role == 'ADMIN' or getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False):
            return True

        if self.uploaded_by and str(self.uploaded_by) == user_id_str:
            return True

        if self.visibility == 'SHARED':
            if user_id_str in [str(u) for u in (self.shared_with_users or [])]:
                return True
            tenant_id = getattr(user, 'tenant_id', None)
            if tenant_id and str(tenant_id) in [str(t) for t in (self.shared_with_tenants or [])]:
                return True

        return False

    def __str__(self):
        return f"MediaFile {self.id} ({self.original_filename}) [{self.visibility}]"
