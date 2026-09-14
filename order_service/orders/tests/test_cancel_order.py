import uuid
from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from orders.models import Order, SubOrder

class DummyUser:
    def __init__(self, user_id):
        self.id = user_id
        self.is_authenticated = True
        self.is_superuser = False
        self.is_adminuser = False

class OrderCancellationTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer_id = uuid.uuid4()
        self.user = DummyUser(self.customer_id)

        self.order = Order.objects.create(
            customer_id=self.customer_id,
            total_amount=Decimal("49.99"),
            status="PENDING"
        )
        self.suborder = SubOrder.objects.create(
            order=self.order,
            status="PENDING",
            vendor_total=Decimal("49.99")
        )

    def test_cancel_order_successfully(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f"/api/orders/{self.order.id}/cancel/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.suborder.refresh_from_db()

        self.assertEqual(self.order.status, "CANCELLED")
        self.assertEqual(self.suborder.status, "CANCELLED")

    def test_cancel_already_cancelled_order(self):
        self.order.status = "CANCELLED"
        self.order.save()

        self.client.force_authenticate(user=self.user)
        response = self.client.post(f"/api/orders/{self.order.id}/cancel/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("already cancelled", response.data.get("message", "").lower())
