import uuid
import sys
from unittest.mock import patch, MagicMock, PropertyMock

# Mock the protobuf modules before they are imported by orders.views
mock_pb2 = MagicMock()
mock_pb2_grpc = MagicMock()
sys.modules.setdefault('orders.catalog_pb2', mock_pb2)
sys.modules.setdefault('orders.catalog_pb2_grpc', mock_pb2_grpc)

from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from orders.models import Order, OutboxEvent, SubOrder, OrderItem, ProcessedEvent
from orders.saga_consumer import process_inventory_reserved, process_inventory_failed, process_payment_failed


def make_catalog_response(found=True, price=10.0, stock=100, error=''):
    mock = MagicMock()
    mock.found = found
    mock.price = price
    mock.stock_count = stock
    mock.title = 'Test Product'
    mock.error_message = error
    return mock


class CreateOrderViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username='orderuser', password='pass123')
        self.client.force_authenticate(user=self.user)
        self.url = reverse('order_create')
        self.product_id = uuid.uuid4()
        self.shipping_address = {
            'full_name': 'Test User',
            'address_line_1': '123 Main St',
            'city': 'Testville',
            'country': 'US'
        }

    @patch('orders.views.requests.post')
    @patch('orders.views.get_catalog_product')
    def test_create_order_success(self, mock_catalog, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {}
        mock_post.return_value = mock_resp

        mock_catalog.return_value = make_catalog_response(found=True, price=25.00, stock=10)
        data = {
            'product_id': str(self.product_id),
            'quantity': 2,
            'shipping_address': self.shipping_address
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.quantity, 2)
        self.assertEqual(order.total_amount, Decimal('50.00'))
        self.assertEqual(order.status, 'PENDING')

    @patch('orders.views.requests.post')
    @patch('orders.views.get_catalog_product')
    def test_create_order_creates_outbox_event(self, mock_catalog, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {}
        mock_post.return_value = mock_resp

        mock_catalog.return_value = make_catalog_response(found=True, price=10.00, stock=5)
        self.client.post(self.url, {
            'product_id': str(self.product_id),
            'quantity': 1,
            'shipping_address': self.shipping_address
        }, format='json')
        self.assertEqual(OutboxEvent.objects.filter(event_type='order.created').count(), 1)

    @patch('orders.views.get_catalog_product')
    def test_create_order_product_not_found(self, mock_catalog):
        mock_catalog.return_value = make_catalog_response(found=False, error='Not found')
        response = self.client.post(self.url, {
            'product_id': str(self.product_id),
            'quantity': 1,
            'shipping_address': self.shipping_address
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('orders.views.get_catalog_product')
    def test_create_order_insufficient_stock(self, mock_catalog):
        mock_catalog.return_value = make_catalog_response(found=True, price=10.00, stock=2)
        response = self.client.post(self.url, {
            'product_id': str(self.product_id),
            'quantity': 5,
            'shipping_address': self.shipping_address
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('out of stock or has insufficient quantity available', response.data['error'])

    @patch('orders.views.get_catalog_product')
    def test_create_order_catalog_service_failure(self, mock_catalog):
        mock_catalog.side_effect = Exception('gRPC error')
        response = self.client.post(self.url, {
            'product_id': str(self.product_id),
            'quantity': 1,
            'shipping_address': self.shipping_address
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    def test_create_order_unauthenticated_fails(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.url, {
            'product_id': str(self.product_id),
            'quantity': 1,
            'shipping_address': self.shipping_address
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_order_invalid_quantity_fails(self):
        response = self.client.post(self.url, {
            'product_id': str(self.product_id),
            'quantity': 0,
            'shipping_address': self.shipping_address
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_order_missing_product_id_fails(self):
        response = self.client.post(self.url, {
            'quantity': 1,
            'shipping_address': self.shipping_address
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class InitiateOrderPaymentViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username='payinitiator', password='pass123')
        self.client.force_authenticate(user=self.user)
        self.order = Order.objects.create(
            customer_id=self.user.id,
            product_id=uuid.uuid4(),
            quantity=1,
            total_amount=Decimal('30.00'),
            status='PENDING'
        )

    @patch('orders.views.requests.post')
    def test_initiate_payment_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.json.return_value = {'payment': {'polar_checkout_id': 'chk_123'}, 'checkout_url': 'https://polar.sh/checkout/chk_123'}
        mock_post.return_value = mock_resp
        url = reverse('order_pay', kwargs={'order_id': self.order.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.order.refresh_from_db()
        self.assertEqual(self.order.polar_checkout_id, 'chk_123')

    @patch('orders.views.requests.post')
    def test_initiate_payment_service_error(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = 'Internal Server Error'
        mock_post.return_value = mock_resp
        url = reverse('order_pay', kwargs={'order_id': self.order.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @patch('orders.views.requests.post')
    def test_initiate_payment_connection_error(self, mock_post):
        mock_post.side_effect = Exception('Connection refused')
        url = reverse('order_pay', kwargs={'order_id': self.order.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    def test_initiate_payment_order_not_found(self):
        url = reverse('order_pay', kwargs={'order_id': uuid.uuid4()})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_initiate_payment_other_user_order_not_found(self):
        from django.contrib.auth.models import User
        other = User.objects.create_user(username='other', password='pass123')
        order = Order.objects.create(
            customer_id=other.id, product_id=uuid.uuid4(),
            quantity=1, total_amount=Decimal('10.00'), status='PENDING'
        )
        url = reverse('order_pay', kwargs={'order_id': order.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class OrderListViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username='listorder', password='pass123')
        self.client.force_authenticate(user=self.user)
        self.url = reverse('order_list')

    def test_list_returns_own_orders(self):
        Order.objects.create(customer_id=self.user.id, product_id=uuid.uuid4(),
                             quantity=1, total_amount=Decimal('10.00'), status='PENDING')
        Order.objects.create(customer_id=uuid.uuid4(), product_id=uuid.uuid4(),
                             quantity=1, total_amount=Decimal('20.00'), status='PENDING')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1)

    def test_list_unauthenticated_fails(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_filter_by_status(self):
        Order.objects.create(customer_id=self.user.id, product_id=uuid.uuid4(),
                             quantity=1, total_amount=Decimal('10.00'), status='PENDING')
        Order.objects.create(customer_id=self.user.id, product_id=uuid.uuid4(),
                             quantity=1, total_amount=Decimal('20.00'), status='PAID')
        response = self.client.get(self.url, {'status': 'PAID'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['status'], 'PAID')


class OutboxListViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        from django.contrib.auth.models import User
        self.tid = uuid.uuid4()
        self.user = User.objects.create_user(username='outboxuser', password='pass123')
        self.user.tenant_id = self.tid
        self.user.save()
        self.client.force_authenticate(user=self.user)
        self.url = reverse('outbox_list')

    def test_list_outbox_events(self):
        OutboxEvent.objects.create(event_type='order.created', payload={'order_id': str(uuid.uuid4()), 'tenant_id': str(self.tid)}, status='PENDING')
        OutboxEvent.objects.create(event_type='order.created', payload={'order_id': str(uuid.uuid4()), 'tenant_id': str(self.tid)}, status='PROCESSED')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 2)

    def test_list_outbox_filter_by_status(self):
        OutboxEvent.objects.create(event_type='order.created', payload={'tenant_id': str(self.tid)}, status='PENDING')
        OutboxEvent.objects.create(event_type='order.created', payload={'tenant_id': str(self.tid)}, status='PROCESSED')
        response = self.client.get(self.url, {'status': 'PENDING'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1)

    def test_list_outbox_unauthenticated_fails(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class DispatchOrderViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username='shopowner', password='pass123')
        self.tenant_id = uuid.uuid4()
        self.user.role = 'vendor'
        self.user.tenant_id = str(self.tenant_id)
        self.client.force_authenticate(user=self.user)
        self.order = Order.objects.create(
            customer_id=10,
            tenant_id=self.tenant_id,
            product_id=uuid.uuid4(),
            quantity=2,
            total_amount=Decimal('100.00'),
            status='PAID'
        )
        self.suborder = SubOrder.objects.create(
            order=self.order,
            vendor_id=str(self.tenant_id),
            status='PAID',
            vendor_total=Decimal('100.00')
        )
        self.item = OrderItem.objects.create(
            order=self.order,
            suborder=self.suborder,
            product_id=self.order.product_id,
            product_name='Test Widget',
            unit_price=Decimal('50.00'),
            quantity=2
        )

    @patch('orders.views.requests.post')
    def test_dispatch_order_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'status': 'committed'}
        mock_post.return_value = mock_resp

        url = reverse('order_dispatch', kwargs={'order_id': self.order.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.order.refresh_from_db()
        self.suborder.refresh_from_db()
        self.assertEqual(self.order.status, 'SHIPPED')
        self.assertEqual(self.suborder.status, 'SHIPPED')
        self.assertEqual(OutboxEvent.objects.filter(event_type='order.shipped').count(), 1)


class OrderSagaTests(TestCase):
    def setUp(self):
        self.customer_id = uuid.uuid4()
        self.order = Order.objects.create(
            customer_id=self.customer_id,
            total_amount=Decimal('100.00'),
            status='PENDING'
        )
        self.event_id = str(uuid.uuid4())

    def test_inventory_reserved_confirms_order(self):
        payload = {'order_id': str(self.order.id)}
        process_inventory_reserved(self.event_id, payload)

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'PAID')
        self.assertTrue(OutboxEvent.objects.filter(event_type='order.confirmed').exists())
        self.assertTrue(ProcessedEvent.objects.filter(event_id=self.event_id).exists())

    def test_inventory_failed_triggers_payment_refund_compensating_event(self):
        payload = {'order_id': str(self.order.id), 'reason': 'Out of stock'}
        process_inventory_failed(self.event_id, payload)

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'FAILED')
        self.assertTrue(OutboxEvent.objects.filter(event_type='payment.refund').exists())
        self.assertTrue(ProcessedEvent.objects.filter(event_id=self.event_id).exists())

    def test_payment_failed_triggers_inventory_release_compensating_event(self):
        payload = {'order_id': str(self.order.id), 'reason': 'Payment declined'}
        process_payment_failed(self.event_id, payload)

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'FAILED')
        self.assertTrue(OutboxEvent.objects.filter(event_type='inventory.release').exists())
        self.assertTrue(ProcessedEvent.objects.filter(event_id=self.event_id).exists())


