import uuid
from django.db import models

class Shipping(models.Model):
    STATUS_CHOICES = (
        ('PREPARING', 'Preparing'),
        ('LABEL_CREATED', 'Label Created'),
        ('SHIPPED', 'Shipped'),
        ('IN_TRANSIT', 'In Transit'),
        ('OUT_FOR_DELIVERY', 'Out for Delivery'),
        ('DELIVERED', 'Delivered'),
        ('FAILED_ATTEMPT', 'Failed Delivery Attempt'),
        ('RETURNED', 'Returned'),
        ('CANCELLED', 'Cancelled'),
    )

    def generate_tracking_code():
        return f"TRK-{uuid.uuid4().hex[:10].upper()}"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, related_name='shipments', null=True, blank=True)
    suborder = models.ForeignKey('orders.SubOrder', on_delete=models.CASCADE, related_name='shipments', null=True, blank=True)
    full_name = models.CharField(max_length=150)
    contact_phone = models.CharField(max_length=30, blank=True, null=True)
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True, null=True)
    postcode = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='USA')
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tracking_code = models.CharField(max_length=100, default=generate_tracking_code, unique=True, db_index=True)
    carrier = models.CharField(max_length=100, default='Standard Delivery')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PREPARING', db_index=True)
    estimated_delivery_date = models.DateField(blank=True, null=True)
    shipped_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Shipping ({self.tracking_code}) - {self.status} to {self.full_name}, {self.city}"

