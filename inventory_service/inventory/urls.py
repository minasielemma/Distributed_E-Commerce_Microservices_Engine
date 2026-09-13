from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WarehouseViewSet,
    InventoryItemViewSet,
    PublicStockCheckView,
    ReserveStockView,
    ReleaseStockView,
    CommitStockView,
    StockMovementListView
)

router = DefaultRouter()
router.register(r'warehouses', WarehouseViewSet, basename='warehouse')
router.register(r'items', InventoryItemViewSet, basename='inventory_item')

urlpatterns = [
    path('public-stock/', PublicStockCheckView.as_view(), name='public_stock_check'),
    path('reserve/', ReserveStockView.as_view(), name='reserve_stock'),
    path('release/', ReleaseStockView.as_view(), name='release_stock'),
    path('commit/', CommitStockView.as_view(), name='commit_stock'),
    path('movements/', StockMovementListView.as_view(), name='stock_movements'),
    path('', include(router.urls)),
]
