from rest_framework import serializers
from django.db.models import Avg
from django.utils.text import slugify
from .models import (
    Category, Product, ProductLike, ProductPrice, PriceDiscount,
    ProductAttribute, ProductAttributeValue, ProductVariant,
    ProductImage, ProductReview, DiscountCode
)

class CategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()
    subcategories_count = serializers.SerializerMethodField()
    products_count = serializers.SerializerMethodField()
    slug = serializers.SlugField(required=False)

    class Meta:
        model = Category
        fields = [
            'id', 'tenant_id', 'name', 'slug', 'parent', 'variant_attributes',
            'subcategories', 'subcategories_count', 'products_count', 'created_at'
        ]

    def get_subcategories(self, obj):
        if obj.subcategories.exists():
            return CategorySerializer(obj.subcategories.all(), many=True).data
        return []

    def get_subcategories_count(self, obj):
        return obj.subcategories.count()

    def get_products_count(self, obj):
        return obj.products.count() + obj.subcategory_products.count()

    def validate(self, attrs):
        base_slug = slugify(attrs.get('slug') or attrs.get('name', ''))
        slug = base_slug
        counter = 1
        instance = self.instance
        while Category.objects.filter(slug=slug).exclude(pk=instance.pk if instance else None).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        attrs['slug'] = slug
        return attrs

class ProductPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductPrice
        fields = ['id', 'base_price', 'cost_price', 'currency']

class PriceDiscountSerializer(serializers.ModelSerializer):
    is_currently_valid = serializers.BooleanField(read_only=True)

    class Meta:
        model = PriceDiscount
        fields = [
            'id', 'tenant_id', 'product', 'category', 'title',
            'discount_type', 'discount_value', 'start_time', 'end_time',
            'is_active', 'priority', 'is_currently_valid', 'created_at'
        ]

class ProductAttributeValueSerializer(serializers.ModelSerializer):
    attribute_name = serializers.CharField(source='attribute.name', read_only=True)

    class Meta:
        model = ProductAttributeValue
        fields = ['id', 'attribute', 'attribute_name', 'value', 'code']

class ProductAttributeSerializer(serializers.ModelSerializer):
    values = ProductAttributeValueSerializer(many=True, read_only=True)
    category = serializers.CharField(required=False, default='COLOR')

    class Meta:
        model = ProductAttribute
        fields = ['id', 'tenant_id', 'name', 'category', 'display_order', 'is_active', 'values', 'created_at']

class ProductImageSerializer(serializers.ModelSerializer):
    image_url = serializers.CharField(max_length=2000)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source='product', required=False, write_only=True
    )
    variant_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.all(), source='variant', required=False, allow_null=True, write_only=True
    )

    class Meta:
        model = ProductImage
        fields = ['id', 'tenant_id', 'product', 'product_id', 'variant', 'variant_id', 'image_url', 'alt_text', 'display_order', 'is_primary', 'created_at']

class ProductVariantSerializer(serializers.ModelSerializer):
    attribute_values_detail = ProductAttributeValueSerializer(source='attribute_values', many=True, read_only=True)
    attribute_value_ids = serializers.PrimaryKeyRelatedField(
        queryset=ProductAttributeValue.objects.all(), many=True, write_only=True, required=False, source='attribute_values'
    )
    effective_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    input_image_url = serializers.CharField(source='image_url', required=False, allow_blank=True, write_only=True)
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = ProductVariant
        fields = [
            'id', 'tenant_id', 'product', 'sku', 'price', 'stock', 'is_active',
            'attribute_values_detail', 'attribute_value_ids', 'effective_price',
            'input_image_url', 'images', 'created_at', 'updated_at'
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        img = instance.images.filter(is_primary=True).first() or instance.images.first()
        if img:
            data['image_url'] = img.image_url
        else:
            prod_img = instance.product.images.filter(is_primary=True).first() or instance.product.images.first()
            data['image_url'] = prod_img.image_url if prod_img else ""
        return data

    def create(self, validated_data):
        img_url = validated_data.pop('image_url', None)
        variant = super().create(validated_data)
        if img_url:
            ProductImage.objects.create(
                product=variant.product,
                variant=variant,
                tenant_id=variant.tenant_id,
                image_url=img_url,
                alt_text=f"{variant.product.name} - {variant.sku}",
                is_primary=True
            )
        return variant

    def update(self, instance, validated_data):
        img_url = validated_data.pop('image_url', None)
        variant = super().update(instance, validated_data)
        if img_url:
            v_img = variant.images.filter(is_primary=True).first() or variant.images.first()
            if v_img:
                v_img.image_url = img_url
                v_img.save()
            else:
                ProductImage.objects.create(
                    product=variant.product,
                    variant=variant,
                    tenant_id=variant.tenant_id,
                    image_url=img_url,
                    alt_text=f"{variant.product.name} - {variant.sku}",
                    is_primary=True
                )
        return variant

class ProductReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductReview
        fields = ['id', 'tenant_id', 'product', 'user_id', 'user_name', 'rating', 'title', 'review_text', 'is_verified_purchase', 'created_at', 'updated_at']
        read_only_fields = ['user_id']

class DiscountCodeSerializer(serializers.ModelSerializer):
    discount_value = serializers.DecimalField(source='value', max_digits=10, decimal_places=2, required=False)
    min_order_amount = serializers.DecimalField(source='min_purchase_amount', max_digits=10, decimal_places=2, required=False)
    max_uses = serializers.IntegerField(source='usage_limit', required=False, allow_null=True)

    class Meta:
        model = DiscountCode
        fields = [
            'id', 'tenant_id', 'code', 'discount_type', 'value', 'discount_value',
            'min_purchase_amount', 'min_order_amount', 'max_discount_amount',
            'valid_from', 'valid_to', 'usage_limit', 'max_uses', 'times_used',
            'is_active', 'created_at'
        ]
        extra_kwargs = {
            'value': {'required': False},
            'min_purchase_amount': {'required': False},
        }

    def validate(self, attrs):
        if 'value' not in attrs and not self.instance:
            raise serializers.ValidationError({'value': 'Discount value is required.'})
        return attrs


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    subcategory_name = serializers.CharField(source='subcategory.name', read_only=True)
    price_detail = ProductPriceSerializer(required=False)
    base_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    dynamic_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    active_discount = PriceDiscountSerializer(read_only=True)
    likes_count = serializers.IntegerField(source='likes.count', read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    input_image_url = serializers.CharField(source='image_url', required=False, allow_blank=True, write_only=True)
    average_rating = serializers.SerializerMethodField()
    reviews = ProductReviewSerializer(many=True, read_only=True)
    reviews_count = serializers.IntegerField(source='reviews.count', read_only=True)
    stock = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'tenant_id', 'name', 'description', 'sku', 'polar_product_id', 'input_image_url',
            'price_detail', 'base_price', 'dynamic_price', 'active_discount',
            'category', 'category_name', 'subcategory', 'subcategory_name',
            'likes_count', 'is_liked', 'variants', 'images', 'reviews', 'average_rating', 'reviews_count',
            'stock', 'created_at', 'updated_at'
        ]

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user and request.user.is_authenticated:
            return obj.likes.filter(user_id=request.user.id).exists()
        return False


    def to_representation(self, instance):
        data = super().to_representation(instance)
        img = instance.images.filter(is_primary=True).first() or instance.images.first()
        data['image_url'] = img.image_url if img else ""
        return data

    def get_average_rating(self, obj):
        avg = obj.reviews.aggregate(Avg('rating'))['rating__avg']
        return round(float(avg), 2) if avg is not None else 0.0

    def get_stock(self, obj):
        # Sum variant stock if variants exist
        variants = obj.variants.all()
        if variants:
            return sum(v.stock for v in variants)
        # Fall back to inventory service DB
        try:
            import os
            from django.db import connections
            inventory_host = os.getenv('INVENTORY_SERVICE_HOST', 'inventory_service')
            import urllib.request, json
            url = f"http://{inventory_host}:8000/api/inventory/items/?product_id={obj.id}"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=2) as resp:
                data = json.loads(resp.read().decode())
                items = data.get('results', data) if isinstance(data, dict) else data
                if isinstance(items, list) and items:
                    return sum(i.get('quantity_available', 0) for i in items)
        except Exception:
            pass
        return 0

    def create(self, validated_data):
        img_url = validated_data.pop('image_url', None)
        price_data = validated_data.pop('price_detail', None)
        product = Product.objects.create(**validated_data)

        if price_data:
            ProductPrice.objects.create(product=product, tenant_id=product.tenant_id, **price_data)
        else:
            ProductPrice.objects.create(product=product, tenant_id=product.tenant_id)

        if img_url:
            ProductImage.objects.create(
                product=product,
                tenant_id=product.tenant_id,
                image_url=img_url,
                alt_text=product.name,
                is_primary=True
            )

        return product

    def update(self, instance, validated_data):
        img_url = validated_data.pop('image_url', None)
        price_data = validated_data.pop('price_detail', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if price_data:
            if hasattr(instance, 'price_detail') and instance.price_detail:
                for attr, value in price_data.items():
                    setattr(instance.price_detail, attr, value)
                instance.price_detail.save()
            else:
                ProductPrice.objects.create(product=instance, tenant_id=instance.tenant_id, **price_data)

        if img_url:
            primary_img = instance.images.filter(is_primary=True).first() or instance.images.first()
            if primary_img:
                primary_img.image_url = img_url
                primary_img.save()
            else:
                ProductImage.objects.create(
                    product=instance,
                    tenant_id=instance.tenant_id,
                    image_url=img_url,
                    alt_text=instance.name,
                    is_primary=True
                )

        return instance

class ProductLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductLike
        fields = ['id', 'user_id', 'product', 'created_at']
