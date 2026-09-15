import uuid
import sys
from unittest.mock import patch, MagicMock

# Mock protobuf modules before orders imports
mock_pb2 = MagicMock()
mock_pb2_grpc = MagicMock()
sys.modules.setdefault('orders.catalog_pb2', mock_pb2)
sys.modules.setdefault('orders.catalog_pb2_grpc', mock_pb2_grpc)

from decimal import Decimal
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from orders.models import Order, OutboxEvent, ProcessedEvent
from orders.saga_consumer import (
    process_inventory_reserved,
    process_inventory_failed,
    process_payment_failed
)


class OrderDownstreamOutageTests(TestCase):
    """
    Tests handling of downstream service outages (e.g. Catalog/Inventory gRPC or HTTP API down).
    """
    def setUp(self):
        self.client = APIClient()
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username='outageuser', password='pass123')
        self.client.force_authenticate(user=self.user)
        self.url = reverse('order_create')
        self.product_id = uuid.uuid4()
        self.shipping_address = {
            'full_name': 'Test User',
            'address_line_1': '123 Main St',
            'city': 'Testville',
            'country': 'US'
        }

    @patch('orders.views.get_catalog_product')
    def test_catalog_service_grpc_outage_returns_503(self, mock_catalog):
        # Simulate gRPC connection failure to catalog service
        mock_catalog.side_effect = Exception("gRPC UNAVAILABLE: Failed to connect to catalog service")
        response = self.client.post(self.url, {
            'product_id': str(self.product_id),
            'quantity': 1,
            'shipping_address': self.shipping_address
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(OutboxEvent.objects.count(), 0)

    @patch('orders.views.create_payment_checkout_grpc')
    def test_payment_service_outage_on_checkout_initiation(self, mock_checkout):
        # Create pending order
        order = Order.objects.create(
            customer_id=self.user.id,
            product_id=self.product_id,
            quantity=1,
            total_amount=Decimal('50.00'),
            status='PENDING'
        )
        url = reverse('order_pay', kwargs={'order_id': order.id})

        # Simulate Payment service connection refusal
        mock_checkout.side_effect = Exception("Connection refused by payment service")
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        order.refresh_from_db()
        self.assertEqual(order.status, 'PENDING')



class OrderSagaCompensatingTransactionTests(TestCase):
    """
    Tests for Saga compensating actions when one service fails mid-execution.
    """
    def setUp(self):
        self.customer_id = uuid.uuid4()
        self.order = Order.objects.create(
            customer_id=self.customer_id,
            total_amount=Decimal('150.00'),
            status='PENDING'
        )

    def test_payment_failure_triggers_inventory_release_compensation(self):
        event_id = str(uuid.uuid4())
        payload = {
            'order_id': str(self.order.id),
            'reason': 'Insufficient funds in payment account'
        }

        process_payment_failed(event_id, payload)

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'FAILED')

        # Verify compensating outbox event created
        outbox = OutboxEvent.objects.filter(event_type='inventory.release').first()
        self.assertIsNotNone(outbox)
        self.assertEqual(outbox.payload['order_id'], str(self.order.id))
        self.assertTrue(ProcessedEvent.objects.filter(event_id=event_id).exists())

    def test_inventory_failure_triggers_payment_refund_compensation(self):
        event_id = str(uuid.uuid4())
        payload = {
            'order_id': str(self.order.id),
            'reason': 'Inventory out of stock during reservation'
        }

        process_inventory_failed(event_id, payload)

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'FAILED')

        # Verify compensating payment refund outbox event created
        outbox = OutboxEvent.objects.filter(event_type='payment.refund').first()
        self.assertIsNotNone(outbox)
        self.assertEqual(outbox.payload['order_id'], str(self.order.id))
        self.assertTrue(ProcessedEvent.objects.filter(event_id=event_id).exists())


class OrderIdempotencySagaTests(TestCase):
    """
    Tests duplicate saga events handling in order service.
    """
    def setUp(self):
        self.order = Order.objects.create(
            customer_id=uuid.uuid4(),
            total_amount=Decimal('75.00'),
            status='PENDING'
        )
        self.event_id = str(uuid.uuid4())

    def test_duplicate_inventory_reserved_event_processed_once(self):
        payload = {'order_id': str(self.order.id)}

        process_inventory_reserved(self.event_id, payload)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'PAID')

        # Second delivery of same event
        process_inventory_reserved(self.event_id, payload)
        self.assertEqual(OutboxEvent.objects.filter(event_type='order.confirmed').count(), 1)
        self.assertEqual(ProcessedEvent.objects.filter(event_id=self.event_id).count(), 1)
