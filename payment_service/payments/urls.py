from django.urls import path
from .views import (
    CreateCheckoutSessionView,
    ConfirmPaymentSessionView,
    PolarWebhookView,
    PaymentListView
)

urlpatterns = [
    path('checkout/', CreateCheckoutSessionView.as_view(), name='payment_checkout'),
    path('confirm/', ConfirmPaymentSessionView.as_view(), name='payment_confirm'),
    path('list/', PaymentListView.as_view(), name='payment_list'),
    path('webhooks/polar/', PolarWebhookView.as_view(), name='polar_webhook'),
]
