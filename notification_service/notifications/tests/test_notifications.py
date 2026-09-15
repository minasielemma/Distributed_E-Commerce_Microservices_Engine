from django.test import TestCase
from rest_framework.test import APIClient
from notifications.models import Notification
from notifications.kafka_consumer import process_notification_message
import uuid

class NotificationModelTests(TestCase):
    def test_create_notification(self):
        notif = Notification.objects.create(
            user_id="123",
            title="Order Delivered",
            message="Your order has been delivered successfully.",
            notification_type="ORDER",
            metadata={"order_id": "ORD-999"}
        )
        self.assertIsNotNone(notif.id)
        self.assertEqual(notif.user_id, "123")
        self.assertFalse(notif.is_read)
        self.assertEqual(notif.notification_type, "ORDER")

class NotificationKafkaConsumerTests(TestCase):
    def test_process_notification_message(self):
        msg = {
            "event_type": "order.shipped",
            "payload": {
                "user_id": "456",
                "title": "Order Shipped",
                "message": "Order #1001 is on the way",
                "notification_type": "ORDER",
                "metadata": {"order_id": "1001"}
            }
        }
        created_notifs = process_notification_message(msg)
        self.assertEqual(len(created_notifs), 1)
        notif = created_notifs[0]
        self.assertEqual(notif.user_id, "456")
        self.assertEqual(notif.title, "Order Shipped")
        self.assertEqual(notif.message, "Order #1001 is on the way")

class NotificationAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.notif1 = Notification.objects.create(
            user_id="789",
            title="Payment Received",
            message="Payment of $50 confirmed",
            notification_type="PAYMENT"
        )

    def test_unread_count_unauthenticated(self):
        response = self.client.get('/api/notifications/unread_count/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['unread_count'], 0)

    def test_create_internal_dispatches(self):
        response = self.client.post('/api/notifications/create-internal/', {
            "user_id": "789",
            "title": "System Update",
            "message": "Maintenance scheduled",
            "notification_type": "SYSTEM"
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['status'], 'queued')
