import uuid
import json
import hmac
import hashlib
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from payments.models import Payment, OutboxEvent, ProcessedEvent
from payments.saga_consumer import process_order_created, process_payment_refund


class CreateCheckoutSessionViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        from django.contrib.auth.models import User as DjangoUser
        self.user = DjangoUser.objects.create_user(username='payuser', password='pass123')
        self.user.id = uuid.uuid4()
        self.client.force_authenticate(user=self.user)
        self.url = reverse('payment_checkout')

    @patch('payments.views.post_order_payment_journal_entry')
    @patch('payments.views.PolarPaymentProvider')
    def test_checkout_success(self, MockProvider, mock_journal):
        mock_instance = MockProvider.return_value
        mock_instance.create_checkout_session.return_value = {
            'checkout_id': 'polar_chk_abc123',
            'checkout_url': 'https://polar.sh/checkout/polar_chk_abc123'
        }
        data = {'order_id': str(uuid.uuid4()), 'amount': '99.99'}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('checkout_url', response.data)
        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(Payment.objects.first().status, 'PENDING')

    @patch('payments.views.post_order_payment_journal_entry')
    @patch('payments.views.PolarPaymentProvider')
    def test_checkout_creates_payment_with_correct_fields(self, MockProvider, mock_journal):
        order_id = uuid.uuid4()
        mock_instance = MockProvider.return_value
        mock_instance.create_checkout_session.return_value = {
            'checkout_id': 'polar_chk_xyz',
            'checkout_url': 'https://polar.sh/checkout/polar_chk_xyz'
        }
        self.client.post(self.url, {'order_id': str(order_id), 'amount': '50.00'})
        payment = Payment.objects.first()
        self.assertEqual(str(payment.order_id), str(order_id))
        self.assertEqual(payment.provider, 'POLAR')
        self.assertEqual(payment.polar_checkout_id, 'polar_chk_xyz')

    def test_checkout_unauthenticated_fails(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.url, {'order_id': str(uuid.uuid4()), 'amount': '10.00'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PaymentSagaTests(TestCase):
    def setUp(self):
        self.order_id = str(uuid.uuid4())
        self.customer_id = str(uuid.uuid4())
        self.event_id = str(uuid.uuid4())

    def test_process_order_created_success(self):
        payload = {
            'order_id': self.order_id,
            'customer_id': self.customer_id,
            'total_amount': '150.00'
        }
        process_order_created(self.event_id, payload)

        payment = Payment.objects.get(order_id=self.order_id)
        self.assertEqual(payment.status, 'PAID')
        self.assertTrue(OutboxEvent.objects.filter(event_type='payment.succeeded').exists())
        self.assertTrue(ProcessedEvent.objects.filter(event_id=self.event_id).exists())

    def test_process_order_created_idempotency(self):
        payload = {
            'order_id': self.order_id,
            'customer_id': self.customer_id,
            'total_amount': '150.00'
        }
        process_order_created(self.event_id, payload)
        process_order_created(self.event_id, payload)

        self.assertEqual(Payment.objects.filter(order_id=self.order_id).count(), 1)
        self.assertEqual(ProcessedEvent.objects.filter(event_id=self.event_id).count(), 1)

    def test_process_payment_refund_compensating_transaction(self):
        payload = {
            'order_id': self.order_id,
            'customer_id': self.customer_id,
            'total_amount': '100.00'
        }
        process_order_created(self.event_id, payload)

        refund_event_id = str(uuid.uuid4())
        refund_payload = {'order_id': self.order_id}
        process_payment_refund(refund_event_id, refund_payload)

        payment = Payment.objects.get(order_id=self.order_id)
        self.assertEqual(payment.status, 'REFUNDED')
        self.assertTrue(OutboxEvent.objects.filter(event_type='payment.refunded').exists())


class PolarCheckoutViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.payment_id = uuid.uuid4()
        self.order_id = uuid.uuid4()
        self.payment = Payment.objects.create(
            id=self.payment_id,
            order_id=self.order_id,
            customer_id=uuid.uuid4(),
            amount=99.99,
            status='PENDING',
            provider='POLAR'
        )

    @patch('payments.views.post_order_payment_journal_entry')
    @patch('payments.grpc_client.mark_order_paid_grpc')
    def test_polar_checkout_get_success(self, mock_mark_paid, mock_journal):
        url = reverse('polar_checkout', kwargs={'payment_id': str(self.payment_id)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'PAID')
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'PAID')

    def test_polar_checkout_not_found(self):
        url = reverse('polar_checkout', kwargs={'payment_id': str(uuid.uuid4())})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

