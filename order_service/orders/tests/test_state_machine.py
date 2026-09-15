import uuid
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

from orders.models import Order, Shipping
from orders.state_machine import OrderStateMachine, OrderState, InvalidStateTransitionError

User = get_user_model()


class OrderStateMachineUnitTests(TestCase):
    def setUp(self):
        self.order = Order.objects.create(
            customer_id=uuid.uuid4(),
            quantity=1,
            total_amount=Decimal('49.99'),
            status='PENDING'
        )

    def test_unpaid_order_cannot_be_shipped_via_state_machine(self):
        """Rule: Unpaid order (PENDING) must not be shipped."""
        self.assertEqual(self.order.status, 'PENDING')
        with self.assertRaises(InvalidStateTransitionError) as ctx:
            OrderStateMachine.validate_transition(self.order, OrderState.SHIPPED)
        self.assertIn("Unpaid order", str(ctx.exception))
        self.assertIn("must be PAID before shipping", str(ctx.exception))

    def test_unpaid_order_cannot_be_delivered_via_state_machine(self):
        """Rule: Unpaid order (PENDING) must not be delivered."""
        with self.assertRaises(InvalidStateTransitionError):
            OrderStateMachine.validate_transition(self.order, OrderState.DELIVERED)

    def test_valid_transitions_from_pending(self):
        """Pending order can transition to PAID, CANCELLED, or FAILED."""
        self.assertTrue(OrderStateMachine.can_transition('PENDING', 'PAID'))
        self.assertTrue(OrderStateMachine.can_transition('PENDING', 'CANCELLED'))
        self.assertTrue(OrderStateMachine.can_transition('PENDING', 'FAILED'))
        self.assertFalse(OrderStateMachine.can_transition('PENDING', 'SHIPPED'))
        self.assertFalse(OrderStateMachine.can_transition('PENDING', 'DELIVERED'))

    def test_paid_order_can_be_shipped(self):
        """Paid order can transition to SHIPPED."""
        self.order.status = 'PAID'
        self.order.save()
        self.assertTrue(OrderStateMachine.can_transition('PAID', 'SHIPPED'))
        self.order.transition_to('SHIPPED')
        self.assertEqual(self.order.status, 'SHIPPED')

    def test_shipped_order_can_be_delivered(self):
        """Shipped order can transition to DELIVERED."""
        self.order.status = 'PAID'
        self.order.save()
        self.order.transition_to('SHIPPED')
        self.order.transition_to('DELIVERED')
        self.assertEqual(self.order.status, 'DELIVERED')

    def test_cancelled_order_cannot_transition(self):
        """Cancelled order is terminal."""
        self.order.status = 'CANCELLED'
        self.order.save()
        self.assertFalse(OrderStateMachine.can_transition('CANCELLED', 'SHIPPED'))
        self.assertFalse(OrderStateMachine.can_transition('CANCELLED', 'PAID'))


class DispatchUnpaidOrderApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(username='admin_sm', password='pass', is_staff=True, is_superuser=True)
        self.admin.role = 'ADMIN'
        self.admin.save()
        self.client.force_authenticate(user=self.admin)

        self.unpaid_order = Order.objects.create(
            customer_id=uuid.uuid4(),
            quantity=1,
            total_amount=Decimal('100.00'),
            status='PENDING'
        )

    def test_dispatch_unpaid_order_fails(self):
        """API rule: Dispatching an unpaid order returns 400 Bad Request."""
        url = reverse('order_dispatch', kwargs={'order_id': self.unpaid_order.id})
        response = self.client.post(url, {'carrier': 'Express Carrier'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Unpaid order', response.data['error'])
        self.unpaid_order.refresh_from_db()
        self.assertEqual(self.unpaid_order.status, 'PENDING')

    def test_create_shipment_for_unpaid_order_fails(self):
        """API rule: Creating a shipment for an unpaid order returns 400 Bad Request."""
        url = reverse('order_shipments', kwargs={'order_id': self.unpaid_order.id})
        response = self.client.post(url, {
            'carrier': 'Standard Carrier',
            'full_name': 'John Doe',
            'address_line_1': '123 Test St',
            'city': 'Sample City',
            'postcode': '12345',
            'country': 'USA'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Unpaid order', response.data['error'])

    def test_dispatch_paid_order_succeeds(self):
        """API rule: Dispatching a PAID order succeeds."""
        self.unpaid_order.status = 'PAID'
        self.unpaid_order.save()

        url = reverse('order_dispatch', kwargs={'order_id': self.unpaid_order.id})
        response = self.client.post(url, {'carrier': 'Express Carrier'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.unpaid_order.refresh_from_db()
        self.assertEqual(self.unpaid_order.status, 'SHIPPED')
