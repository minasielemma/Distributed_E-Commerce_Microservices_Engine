import uuid
from unittest.mock import patch, MagicMock, PropertyMock
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from orders.models import Order, OutboxEvent, SubOrder, OrderItem, ProcessedEvent
from orders.saga_consumer import process_inventory_reserved, process_inventory_failed, process_payment_failed


def make_catalog_response(found=True, price=10.0, stock=100, tenant_id='11111111-1111-1111-1111-111111111111', error=''):
    mock = MagicMock()
    mock.found = found
    mock.price = price
    mock.stock_count = stock
    mock.title = 'Test Product'
    mock.tenant_id = tenant_id
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

    @patch('orders.views.check_inventory_stock')
    @patch('orders.views.get_catalog_product')
    def test_create_order_success(self, mock_catalog, mock_inventory):
        mock_catalog.return_value = make_catalog_response(found=True, price=25.00, stock=10)
        mock_inv = MagicMock()
        mock_inv.is_available = True
        mock_inventory.return_value = mock_inv
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

    @patch('orders.views.check_inventory_stock')
    @patch('orders.views.get_catalog_product')
    def test_create_order_creates_outbox_event(self, mock_catalog, mock_inventory):
        mock_catalog.return_value = make_catalog_response(found=True, price=25.00, stock=10)
        mock_inv = MagicMock()
        mock_inv.is_available = True
        mock_inventory.return_value = mock_inv
        data = {
            'product_id': str(self.product_id),
            'quantity': 2,
            'shipping_address': self.shipping_address
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        outbox = OutboxEvent.objects.filter(event_type='order.created').first()
        self.assertIsNotNone(outbox)
        self.assertEqual(outbox.payload['items'][0]['quantity'], 2)
        order = Order.objects.first()
        self.assertEqual(order.shipping_address['city'], 'Testville')

    @patch('orders.views.get_catalog_product')
    def test_create_order_product_not_found(self, mock_catalog):
        mock_catalog.return_value = make_catalog_response(found=False, error='Product not found')
        data = {
            'product_id': str(self.product_id),
            'quantity': 1,
            'shipping_address': self.shipping_address
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('orders.views.get_catalog_product')
    def test_create_order_insufficient_stock(self, mock_catalog):
        mock_catalog.return_value = make_catalog_response(found=True, price=10.0, stock=1)
        data = {
            'product_id': str(self.product_id),
            'quantity': 5,
            'shipping_address': self.shipping_address
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('orders.views.get_catalog_product')
    def test_create_order_catalog_service_down(self, mock_catalog):
        mock_catalog.return_value = None
        data = {
            'product_id': str(self.product_id),
            'quantity': 1,
            'shipping_address': self.shipping_address
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)


    def test_create_order_unauthenticated(self):
        self.client.logout()
        data = {
            'product_id': str(self.product_id),
            'quantity': 1,
            'shipping_address': self.shipping_address
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class InitiateOrderPaymentViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username='orderuser2', password='pass123')
        self.client.force_authenticate(user=self.user)
        self.order = Order.objects.create(
            customer_id=self.user.id,
            product_id=uuid.uuid4(),
            quantity=1,
            total_amount=Decimal('30.00'),
            status='PENDING'
        )

    @patch('orders.views.create_payment_checkout_grpc')
    def test_initiate_payment_success(self, mock_checkout):
        mock_res = MagicMock()
        mock_res.success = True
        mock_res.status = 'PENDING'
        mock_res.payment_id = 'pay_123'
        mock_res.checkout_url = 'https://polar.sh/checkout/chk_123'
        mock_checkout.return_value = mock_res

        url = reverse('order_pay', kwargs={'order_id': self.order.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['payment']['checkout_url'], 'https://polar.sh/checkout/chk_123')

    @patch('orders.views.create_payment_checkout_grpc')
    def test_initiate_payment_service_error(self, mock_checkout):
        mock_res = MagicMock()
        mock_res.success = False
        mock_res.error_message = 'Internal Server Error'
        mock_checkout.return_value = mock_res

        url = reverse('order_pay', kwargs={'order_id': self.order.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @patch('orders.views.create_payment_checkout_grpc')
    def test_initiate_payment_connection_error(self, mock_checkout):
        mock_checkout.side_effect = Exception("Connection refused by payment service")
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

    @patch('orders.views.commit_stock_grpc')
    def test_dispatch_order_success(self, mock_commit):
        mock_res = MagicMock()
        mock_res.success = True
        mock_commit.return_value = mock_res


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


class CarrierTrackingTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_get_tracking_url_resolution(self):
        from orders.carriers import get_tracking_url
        self.assertEqual(
            get_tracking_url('FedEx', '123456'),
            'https://www.fedex.com/fedextrack/?trknbr=123456'
        )
        self.assertEqual(
            get_tracking_url('UPS', '1Z999999'),
            'https://www.ups.com/track?tracknum=1Z999999'
        )
        self.assertEqual(
            get_tracking_url('USPS', '94001000'),
            'https://tools.usps.com/go/TrackConfirmAction?tLabels=94001000'
        )
        self.assertEqual(
            get_tracking_url('DHL', '777888'),
            'https://www.dhl.com/en/express/tracking.html?AWB=777888'
        )
        self.assertIsNone(get_tracking_url('Standard Delivery', 'TRK123'))
        self.assertIsNone(get_tracking_url('Unknown Carrier', '123'))

    def test_available_carriers_endpoint(self):
        url = reverse('available_carriers')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = response.data.get('names', [])
        self.assertIn('FedEx', names)
        self.assertIn('UPS', names)
        self.assertIn('USPS', names)
        self.assertIn('DHL', names)
        self.assertIn('Standard Delivery', names)

