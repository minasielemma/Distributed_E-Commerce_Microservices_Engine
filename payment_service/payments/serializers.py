from rest_framework import serializers
from .models import Payment

class CreateCheckoutSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    tenant_id = serializers.UUIDField(required=False, allow_null=True)

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'tenant_id', 'order_id', 'customer_id', 'amount', 'provider', 'status', 'polar_checkout_id', 'polar_checkout_url', 'created_at', 'updated_at']
