from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, ProductViewSet, StorefrontProductViewSet, StorefrontCategoryViewSet, PriceDiscountViewSet,
    ProductAttributeViewSet, ProductAttributeValueViewSet,
    ProductVariantViewSet, ProductImageViewSet,
    ProductReviewViewSet, DiscountCodeViewSet
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'storefront/products', StorefrontProductViewSet, basename='storefront-product')
router.register(r'storefront/categories', StorefrontCategoryViewSet, basename='storefront-category')
router.register(r'discounts', PriceDiscountViewSet, basename='discount')
router.register(r'attributes', ProductAttributeViewSet, basename='attribute')
router.register(r'attribute-values', ProductAttributeValueViewSet, basename='attribute-value')
router.register(r'variants', ProductVariantViewSet, basename='variant')
router.register(r'images', ProductImageViewSet, basename='image')
router.register(r'reviews', ProductReviewViewSet, basename='review')
router.register(r'coupons', DiscountCodeViewSet, basename='coupon')

urlpatterns = [
    path('', include(router.urls)),
]
