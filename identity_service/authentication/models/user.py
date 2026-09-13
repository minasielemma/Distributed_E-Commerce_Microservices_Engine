import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('PLATFORM_ADMIN', 'Platform Admin'),
        ('STORE_OWNER', 'Store Owner / Tenant'),
        ('CUSTOMER', 'Customer'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='STORE_OWNER', db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
            models.Index(fields=['role']),
        ]

    def __str__(self):
        return f"{self.username} ({self.role}) ({self.id})"

