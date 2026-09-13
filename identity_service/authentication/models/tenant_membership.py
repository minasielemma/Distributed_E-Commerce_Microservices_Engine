import uuid
from django.db import models
from .user import User
from .tenant import Tenant

DEFAULT_ROLE_PERMISSIONS = {
    'SHOP_OWNER': [
        'products.read', 'products.create', 'products.update', 'products.delete',
        'categories.manage', 'coupons.manage',
        'orders.read', 'orders.update', 'orders.cancel', 'orders.refund',
        'inventory.read', 'inventory.update', 'inventory.manage',
        'customers.read', 'customers.update',
        'finance.read', 'finance.manage', 'invoices.manage',
        'staff.read', 'staff.invite', 'staff.update', 'staff.remove',
        'chat.read', 'chat.send', 'media.upload', 'media.read', 'media.delete'
    ],
    'SHOP_ADMIN': [
        'products.read', 'products.create', 'products.update', 'products.delete',
        'categories.manage', 'coupons.manage',
        'orders.read', 'orders.update', 'orders.cancel',
        'inventory.read', 'inventory.update', 'inventory.manage',
        'customers.read', 'finance.read',
        'chat.read', 'chat.send', 'media.upload', 'media.read', 'media.delete'
    ],
    'PRODUCT_MANAGER': [
        'products.read', 'products.create', 'products.update', 'products.delete',
        'categories.manage', 'coupons.manage',
        'media.upload', 'media.read'
    ],
    'ORDER_MANAGER': [
        'orders.read', 'orders.update', 'orders.cancel',
        'customers.read', 'chat.read', 'chat.send'
    ],
    'INVENTORY_MANAGER': [
        'inventory.read', 'inventory.update', 'inventory.manage',
        'products.read'
    ],
    'CUSTOMER_SUPPORT': [
        'customers.read', 'orders.read', 'chat.read', 'chat.send'
    ],
    'FINANCE_ACCOUNTING': [
        'finance.read', 'finance.manage', 'invoices.manage',
        'orders.refund', 'orders.read'
    ],
    'SHOP_STAFF_LIMITED': [
        'products.read', 'orders.read'
    ]
}

class TenantMembership(models.Model):
    ROLE_CHOICES = (
        ('SHOP_OWNER', 'Shop Owner'),
        ('SHOP_ADMIN', 'Shop Admin'),
        ('PRODUCT_MANAGER', 'Product Manager'),
        ('ORDER_MANAGER', 'Order Manager'),
        ('INVENTORY_MANAGER', 'Inventory Manager'),
        ('CUSTOMER_SUPPORT', 'Customer Support'),
        ('FINANCE_ACCOUNTING', 'Finance & Accounting'),
        ('SHOP_STAFF_LIMITED', 'Limited Staff'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='SHOP_STAFF_LIMITED', db_index=True)
    custom_permissions = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'tenant')
        indexes = [
            models.Index(fields=['user', 'tenant']),
            models.Index(fields=['tenant', 'role']),
        ]

    def get_effective_permissions(self):
        default_perms = DEFAULT_ROLE_PERMISSIONS.get(self.role, [])
        if self.custom_permissions:
            return list(set(default_perms + self.custom_permissions))
        return default_perms

    def __str__(self):
        return f"{self.user.email} in {self.tenant.name} as {self.role}"
