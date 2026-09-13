import uuid
from django.db import models

class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    variant_attributes = models.JSONField(default=list, blank=True)
    is_global = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        indexes = [
            models.Index(fields=['tenant_id', 'parent']),
            models.Index(fields=['tenant_id', 'slug']),
        ]

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} -> {self.name}"
        return self.name
