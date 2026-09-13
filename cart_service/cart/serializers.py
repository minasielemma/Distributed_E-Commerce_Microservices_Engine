from rest_framework import serializers
from .models import Cart, CartItem, Wishlist, WishlistItem, ItemRequest

class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['id', 'cart', 'product_id', 'variant_id', 'variant_name', 'product_name', 'image_url', 'quantity', 'price', 'created_at', 'updated_at']
        read_only_fields = ['cart']

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user_id', 'tenant_id', 'status', 'coupon_code', 'discount_amount', 'subtotal', 'total', 'items', 'created_at', 'updated_at']
        read_only_fields = ['user_id', 'tenant_id', 'subtotal', 'total']


class WishlistItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = WishlistItem
        fields = ['id', 'wishlist', 'product_id', 'product_name', 'image_url', 'price', 'note', 'created_at']
        read_only_fields = ['wishlist']

class WishlistSerializer(serializers.ModelSerializer):
    items = WishlistItemSerializer(many=True, read_only=True)

    class Meta:
        model = Wishlist
        fields = ['id', 'user_id', 'tenant_id', 'name', 'items', 'created_at', 'updated_at']
        read_only_fields = ['user_id', 'tenant_id']

class ItemRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemRequest
        fields = ['id', 'user_id', 'tenant_id', 'product_name', 'description', 'quantity', 'status', 'admin_response', 'created_at', 'updated_at']
        read_only_fields = ['user_id']


class ItemRequestStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemRequest
        fields = ['status', 'admin_response']

