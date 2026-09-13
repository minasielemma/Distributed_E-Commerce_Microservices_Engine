from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CartViewSet, WishlistViewSet, ItemRequestViewSet

router = DefaultRouter()
router.register(r'carts', CartViewSet, basename='cart')
router.register(r'wishlists', WishlistViewSet, basename='wishlist')
router.register(r'item-requests', ItemRequestViewSet, basename='item-request')

urlpatterns = [
    path('clear/', CartViewSet.as_view({'post': 'clear_cart', 'delete': 'clear_cart'}), name='cart_clear'),
    path('', include(router.urls)),
]
