import uuid
from django.db import models

class ProductAttribute(models.Model):
    ATTRIBUTE_CATEGORIES = [
        ('COLOR', 'Color'),
        ('SIZE', 'Size'),
        ('MATERIAL', 'Material'),
        ('STYLE', 'Style'),
        ('FIT', 'Fit'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    name = models.CharField(max_length=50)
    category = models.CharField(max_length=50, blank=True, default='COLOR')
    display_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['display_order', 'name']
        unique_together = ['tenant_id', 'name']

    def __str__(self):
        return f"{self.name} ({self.category})"


class ProductAttributeValue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE, related_name='values')
    value = models.CharField(max_length=100)
    code = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        unique_together = ['attribute', 'value']

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"
