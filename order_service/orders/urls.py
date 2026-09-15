from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CreateOrderView,
    InitiateOrderPaymentView,
    CancelOrderView,
    DispatchOrderView,
    MarkOrderPaidView,
    OutboxListView,
    OrderListView,
    OrderDetailView,
    BroadcastNotificationView,
    AvailableCarriersView
)
from .shipment_views import (
    OrderShipmentListView,
    ShipmentDetailView,
    UpdateShipmentStatusView,
    ShipmentHistoryView,
    PublicTrackingView,
)
router = DefaultRouter()

urlpatterns = [
    path('carriers/', AvailableCarriersView.as_view(), name='available_carriers'),
    path('create/', CreateOrderView.as_view(), name='order_create'),

    path('list/', OrderListView.as_view(), name='order_list'),
    path('<uuid:order_id>/', OrderDetailView.as_view(), name='order_detail'),
    path('<uuid:order_id>/pay/', InitiateOrderPaymentView.as_view(), name='order_pay'),
    path('<uuid:order_id>/mark-paid/', MarkOrderPaidView.as_view(), name='order_mark_paid'),
    path('<uuid:order_id>/cancel/', CancelOrderView.as_view(), name='order_cancel'),
    path('<uuid:order_id>/dispatch/', DispatchOrderView.as_view(), name='order_dispatch'),
    path('<uuid:order_id>/ship/', DispatchOrderView.as_view(), name='order_ship'),
    path('<uuid:order_id>/shipments/', OrderShipmentListView.as_view(), name='order_shipments'),
    path('shipments/<uuid:pk>/', ShipmentDetailView.as_view(), name='shipment_detail'),
    path('shipments/<uuid:pk>/update-status/', UpdateShipmentStatusView.as_view(), name='shipment_update_status'),
    path('shipments/<uuid:pk>/history/', ShipmentHistoryView.as_view(), name='shipment_history'),
    path('track/<str:tracking_code>/', PublicTrackingView.as_view(), name='public_tracking'),
    path('outbox/', OutboxListView.as_view(), name='outbox_list'),
    path('broadcast-notification/', BroadcastNotificationView.as_view(), name='broadcast_notification'),
]



