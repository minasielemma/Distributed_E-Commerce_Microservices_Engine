from rest_framework import serializers
from .models import UserInteraction, ProductMetadataCache, CachedRecommendation

class RecommendationItemSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    score = serializers.FloatField(default=1.0)
    reason = serializers.CharField(default='')
    name = serializers.CharField(default='', required=False)
    price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default=0.00)
    category_name = serializers.CharField(default='', required=False)
    image_url = serializers.CharField(default='', required=False, allow_blank=True)


class TrackViewSerializer(serializers.Serializer):
    product_id = serializers.UUIDField(required=True)
    tenant_id = serializers.UUIDField(required=False, allow_null=True)


class UserInteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserInteraction
        fields = '__all__'


class ProductMetadataCacheSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductMetadataCache
        fields = '__all__'
