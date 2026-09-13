import uuid
import threading
from unittest.mock import patch, MagicMock
from django.test import TransactionTestCase, TestCase
from django.db import connection
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from payments.models import Payment, OutboxEvent, ProcessedEvent
from payments.saga_consumer import process_order_created, process_payment_refund


class ConcurrentPaymentCheckoutTests(TransactionTestCase):
    """
    Tests for race conditions when multiple concurrent requests attempt checkout for the same order.
    """
    def setUp(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username='concur_pay', password='pass123')
        self.user.id = uuid.uuid4()
        self.order_id = str(uuid.uuid4())
        self.url = reverse('payment_checkout')

    @patch('payments.views.post_order_payment_journal_entry')
    @patch('payments.views.PolarPaymentProvider')
    def test_concurrent_checkouts_handled(self, MockProvider, mock_journal):
        mock_instance = MockProvider.return_value
        mock_instance.create_checkout_session.return_value = {
            'checkout_id': 'polar_chk_concurrent',
            'checkout_url': 'https://polar.sh/checkout/polar_chk_concurrent'
        }

        num_threads = 5
        statuses = []
        lock = threading.Lock()

        def do_checkout():
            try:
                client = APIClient()
                client.force_authenticate(user=self.user)
                res = client.post(self.url, {'order_id': self.order_id, 'amount': '100.00'})
                with lock:
                    statuses.append(res.status_code)
            finally:
                connection.close()

        threads = []
        for _ in range(num_threads):
            t = threading.Thread(target=do_checkout)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Checkouts created and idempotent responses
        self.assertTrue(all(s in [status.HTTP_201_CREATED, status.HTTP_200_OK] for s in statuses))
        self.assertEqual(Payment.objects.filter(order_id=self.order_id).count(), 1)


class PaymentProviderOutageTests(TestCase):
    """
    Tests mid-execution errors when external payment provider (Polar API) is unreachable or returns error.
    """
    def setUp(self):
        self.client = APIClient()
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username='provider_fail', password='pass123')
        self.user.id = uuid.uuid4()
        self.client.force_authenticate(user=self.user)
        self.url = reverse('payment_checkout')
        self.order_id = str(uuid.uuid4())

    @patch('payments.views.requests.post')
    @patch('payments.views.PolarPaymentProvider')
    def test_checkout_provider_fallback_to_local_payment(self, MockProvider, mock_post):
        mock_instance = MockProvider.return_value
        # Simulate Polar API returning error dict (unconfigured or API error)
        mock_instance.create_checkout_session.return_value = {
            'error': 'Polar API service unavailable'
        }

        response = self.client.post(self.url, {'order_id': self.order_id, 'amount': '50.00'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'PAID')
        self.assertEqual(Payment.objects.filter(order_id=self.order_id).count(), 1)


class PaymentSagaCompensatingResilienceTests(TestCase):
    """
    Tests idempotency and error handling for payment saga compensating events.
    """
    def setUp(self):
        self.order_id = str(uuid.uuid4())
        self.customer_id = str(uuid.uuid4())
        self.event_id = str(uuid.uuid4())

    def test_process_payment_refund_idempotency(self):
        payload = {
            'order_id': self.order_id,
            'customer_id': self.customer_id,
            'total_amount': '100.00'
        }
        # First process order created
        process_order_created(self.event_id, payload)
        payment = Payment.objects.get(order_id=self.order_id)
        self.assertEqual(payment.status, 'PAID')

        # Now issue refund compensating transaction twice
        refund_event_id = str(uuid.uuid4())
        refund_payload = {'order_id': self.order_id}

        process_payment_refund(refund_event_id, refund_payload)
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'REFUNDED')

        # Duplicate refund event
        process_payment_refund(refund_event_id, refund_payload)
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'REFUNDED')

        # Exactly 1 outbox event for payment.refunded
        self.assertEqual(OutboxEvent.objects.filter(event_type='payment.refunded').count(), 1)
        self.assertEqual(ProcessedEvent.objects.filter(event_id=refund_event_id).count(), 1)
