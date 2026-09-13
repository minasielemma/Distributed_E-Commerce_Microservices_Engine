from rest_framework import serializers
from .models import Warehouse, InventoryItem, StockMovement

class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ['id', 'tenant_id', 'name', 'code', 'address', 'created_at']
        read_only_fields = ['tenant_id']

class InventoryItemSerializer(serializers.ModelSerializer):
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    warehouse_code = serializers.CharField(source='warehouse.code', read_only=True)

    class Meta:
        model = InventoryItem
        fields = [
            'id', 'tenant_id', 'product_id', 'warehouse', 'warehouse_name',
            'warehouse_code', 'quantity_available', 'quantity_reserved',
            'reorder_level', 'updated_at'
        ]
        read_only_fields = ['tenant_id']

class ReserveStockSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)
    reference_id = serializers.CharField(required=False, default='')

class StockMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMovement
        fields = ['id', 'tenant_id', 'inventory_item', 'movement_type', 'quantity', 'reference_id', 'created_at']
