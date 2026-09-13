import uuid
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase
from payments.polar_provider import PolarPaymentProvider
from payments.models import Payment

class PolarProductSyncTestCase(TestCase):
    def setUp(self):
        self.provider = PolarPaymentProvider()

    @patch('payments.polar_provider.requests.post')
    def test_sync_product_to_polar_creates_live_product(self, mock_post):
        """Test on-demand / background syncing of a product to Polar API."""
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.json.return_value = {'id': 'polar_prod_12345'}
        mock_post.return_value = mock_resp

        dummy_product_id = str(uuid.uuid4())
        product_name = f"Test Sync Product {dummy_product_id[:8]}"
        product_price = Decimal("19.99")

        polar_id = self.provider.sync_product_to_polar(
            product_id=dummy_product_id,
            name=product_name,
            price=product_price,
            description="Automated unit test product sync"
        )

        self.assertIsNotNone(polar_id, "Polar product ID should not be None when API key is valid")
        self.assertEqual(polar_id, 'polar_prod_12345')

    @patch('payments.polar_provider.requests.post')
    def test_on_demand_sync_fallback_during_checkout(self, mock_post):
        """Test that missing polar_product_id during checkout automatically triggers on-demand sync."""
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.json.return_value = {
            'id': 'chk_test_123',
            'url': 'https://polar.sh/checkout/chk_test_123'
        }
        mock_post.return_value = mock_resp

        dummy_order_id = str(uuid.uuid4())
        dummy_customer_id = str(uuid.uuid4())
        dummy_catalog_product_id = str(uuid.uuid4())
        amount = Decimal("29.99")

        session_info = self.provider.create_checkout_session(
            order_id=dummy_order_id,
            customer_id=dummy_customer_id,
            amount=amount,
            catalog_product_id=dummy_catalog_product_id,
            product_name="Fallback Test Item"
        )

        self.assertNotIn('error', session_info, f"Checkout creation failed: {session_info.get('details')}")
        self.assertIn('checkout_id', session_info)
        self.assertIn('checkout_url', session_info)

    @patch('payments.polar_provider.requests.get')
    @patch('payments.polar_provider.requests.patch')
    def test_polar_product_price_update_and_matching(self, mock_patch, mock_get):
        """Test that price mismatch between local product and Polar automatically updates Polar product price."""
        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.json.return_value = {"prices": [{"price_amount": 1500}]}
        mock_get.return_value = mock_get_resp

        mock_patch_resp = MagicMock()
        mock_patch_resp.status_code = 200
        mock_patch.return_value = mock_patch_resp

        polar_id = "polar_prod_123"
        updated_price = Decimal("25.00")

        result = self.provider.ensure_polar_product_price_matches(polar_id, updated_price)
        self.assertTrue(mock_patch.called)

    def test_webhook_returns_paid_status(self):
        """Test that Polar webhook marks payment as PAID and returns status PAID."""
        from django.test import Client
        client = Client()

        dummy_order_id = uuid.uuid4()
        payment = Payment.objects.create(
            order_id=dummy_order_id,
            customer_id=uuid.uuid4(),
            amount=Decimal("49.99"),
            provider="POLAR",
            status="PENDING",
            polar_checkout_id="chk_test_123456"
        )

        response = client.post(
            "/api/payments/webhooks/polar/",
            data={"data": {"metadata": {"order_id": str(dummy_order_id)}, "id": "chk_test_123456"}},
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        res_data = response.json()
        self.assertEqual(res_data.get("status"), "PAID")

        payment.refresh_from_db()
        self.assertEqual(payment.status, "PAID")
