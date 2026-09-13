from rest_framework import serializers
from .models import Order, OutboxEvent, SubOrder, OrderItem, Shipping, StatusHistory
from .carriers import get_tracking_url

class OrderItemSerializer(serializers.ModelSerializer):
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product_id', 'variant_id', 'product_name', 'variant_sku', 'unit_price', 'quantity', 'total_price']

class ShippingSerializer(serializers.ModelSerializer):
    tracking_url = serializers.SerializerMethodField()

    class Meta:
        model = Shipping
        fields = [
            'id', 'order', 'suborder', 'full_name', 'contact_phone', 'address_line_1', 'address_line_2',
            'city', 'state', 'postcode', 'country', 'shipping_cost', 'tracking_code', 'carrier',
            'status', 'estimated_delivery_date', 'shipped_at', 'delivered_at', 'notes',
            'tracking_url', 'created_at', 'updated_at'
        ]

    def get_tracking_url(self, obj):
        return get_tracking_url(obj.carrier, obj.tracking_code)

class StatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = StatusHistory
        fields = ['id', 'entity_type', 'entity_id', 'from_status', 'to_status', 'changed_by', 'notes', 'created_at']

class ShipmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shipping
        fields = [
            'order', 'suborder', 'full_name', 'contact_phone', 'address_line_1', 'address_line_2',
            'city', 'state', 'postcode', 'country', 'shipping_cost', 'carrier',
            'status', 'estimated_delivery_date', 'notes'
        ]

class ShipmentStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Shipping.STATUS_CHOICES)
    notes = serializers.CharField(required=False, allow_blank=True, default='')
    carrier = serializers.CharField(required=False, allow_blank=True)
    tracking_code = serializers.CharField(required=False, allow_blank=True)
    estimated_delivery_date = serializers.DateField(required=False, allow_null=True)

class SubOrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    shipments = ShippingSerializer(many=True, read_only=True)

    class Meta:
        model = SubOrder
        fields = ['id', 'vendor_id', 'status', 'vendor_total', 'currency', 'shipped_at', 'delivered_at', 'items', 'shipments', 'created_at']

class CreateOrderItemInputSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    variant_id = serializers.UUIDField(required=False, allow_null=True)
    variant_sku = serializers.CharField(required=False, allow_blank=True, default='')
    product_name = serializers.CharField(required=False, allow_blank=True, default='')
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    quantity = serializers.IntegerField(min_value=1, default=1)

class CreateOrderSerializer(serializers.Serializer):
    product_id = serializers.UUIDField(required=False, allow_null=True)
    quantity = serializers.IntegerField(min_value=1, default=1, required=False)
    items = CreateOrderItemInputSerializer(many=True, required=False)
    shipping_address = serializers.JSONField(required=True)
    billing_address = serializers.JSONField(required=False, default=dict)
    discount_code = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    shipping_cost = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default='0.00')
    tax_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default='0.00')

    def validate_shipping_address(self, value):
        if isinstance(value, str):
            try:
                import json
                value = json.loads(value)
            except (ValueError, TypeError):
                raise serializers.ValidationError('Invalid shipping address format.')
        # Coerce None values to empty string before checking
        required_fields = ['full_name', 'address_line_1', 'city', 'country']
        missing = [f for f in required_fields if not str(value.get(f) or '').strip()]
        if missing:
            raise serializers.ValidationError(
                f'Shipping address is missing required fields: {", ".join(missing)}.'
            )
        return value

    def validate(self, attrs):
        if not attrs.get('product_id') and not attrs.get('items'):
            raise serializers.ValidationError(
                {'product_id': 'Either product_id or items list must be provided.'}
            )
        return attrs

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    suborders = SubOrderSerializer(many=True, read_only=True)
    shipments = ShippingSerializer(many=True, read_only=True)
    shipping_detail = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'tenant_id', 'customer_id', 'product_id', 'quantity',
            'subtotal', 'tax_amount', 'shipping_cost', 'discount_code', 'discount_amount',
            'total_amount', 'currency', 'status', 'polar_checkout_id',
            'shipping_address', 'billing_address', 'items', 'suborders', 'shipments', 'shipping_detail',
            'created_at', 'updated_at'
        ]

    def get_shipping_detail(self, obj):
        first_shipment = obj.shipments.first()
        if first_shipment:
            return ShippingSerializer(first_shipment).data
        return None

class OutboxEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = OutboxEvent
        fields = ['id', 'event_type', 'payload', 'status', 'created_at', 'processed_at']

