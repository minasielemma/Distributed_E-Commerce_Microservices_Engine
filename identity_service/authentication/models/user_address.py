import uuid
from django.db import models
from django.conf import settings

class UserAddress(models.Model):
    ADDRESS_TYPES = [
        ('SHIPPING', 'Shipping Address'),
        ('BILLING', 'Billing Address'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='addresses')
    title = models.CharField(max_length=50, default='Home')
    full_name = models.CharField(max_length=150, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address_type = models.CharField(max_length=20, choices=ADDRESS_TYPES, default='SHIPPING')
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='USA')
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', '-updated_at']
        indexes = [
            models.Index(fields=['user', 'is_default']),
        ]

    def save(self, *args, **kwargs):
        if self.is_default:
            UserAddress.objects.filter(user=self.user, address_type=self.address_type, is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.full_name or self.user.username} ({self.city}, {self.country})"
