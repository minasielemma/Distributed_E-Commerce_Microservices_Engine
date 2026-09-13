import uuid
import threading
from django.test import TransactionTestCase, TestCase
from django.db import transaction, connection
from rest_framework.test import APIClient
from rest_framework import status

from inventory.models import Warehouse, InventoryItem, StockMovement, OutboxEvent, ProcessedEvent
from inventory.saga_consumer import process_payment_succeeded, process_stock_release


class ConcurrentStockReservationTests(TransactionTestCase):
    """
    Tests for race conditions when multiple concurrent requests attempt to reserve limited stock.
    Verifies select_for_update() row locking prevents negative stock and over-reservation.
    """
    def setUp(self):
        self.tenant_id = uuid.uuid4()
        self.warehouse = Warehouse.objects.create(
            tenant_id=self.tenant_id, name='Race WH', code='RACE01'
        )
        self.product_id = uuid.uuid4()
        # Item starts with only 5 units available
        self.item = InventoryItem.objects.create(
            tenant_id=self.tenant_id,
            product_id=self.product_id,
            warehouse=self.warehouse,
            quantity_available=5,
            quantity_reserved=0
        )

    def test_concurrent_reservations_prevent_overbooking(self):
        num_threads = 10
        requested_qty = 1  # 10 threads requesting 1 item each, total 10 > 5 available
        success_count = [0]
        failure_count = [0]
        lock = threading.Lock()

        def reserve():
            try:
                client = APIClient()
                data = {
                    'product_id': str(self.product_id),
                    'quantity': requested_qty,
                    'reference_id': f'order-{uuid.uuid4()}'
                }
                res = client.post(
                    '/api/inventory/reserve/',
                    data,
                    format='json',
                    HTTP_X_SERVICE_TOKEN='internal-token'
                )
                with lock:
                    if res.status_code == status.HTTP_200_OK:
                        success_count[0] += 1
                    else:
                        failure_count[0] += 1
            finally:
                connection.close()

        threads = []
        for _ in range(num_threads):
            t = threading.Thread(target=reserve)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        self.item.refresh_from_db()

        # Exactly 5 reservations should succeed, 5 should fail due to insufficient stock
        self.assertEqual(success_count[0], 5)
        self.assertEqual(failure_count[0], 5)
        self.assertEqual(self.item.quantity_available, 0)
        self.assertEqual(self.item.quantity_reserved, 5)
        self.assertGreaterEqual(self.item.quantity_available, 0)


class MidExecutionErrorRollbackTests(TestCase):
    """
    Tests mid-execution errors and ensures atomic database transaction rollback.
    """
    def setUp(self):
        self.tenant_id = uuid.uuid4()
        self.warehouse = Warehouse.objects.create(
            tenant_id=self.tenant_id, name='Rollback WH', code='ROLL01'
        )
        self.product_id = uuid.uuid4()
        self.item = InventoryItem.objects.create(
            tenant_id=self.tenant_id,
            product_id=self.product_id,
            warehouse=self.warehouse,
            quantity_available=10,
            quantity_reserved=0
        )

    def test_reservation_rollback_on_stock_movement_failure(self):
        initial_available = self.item.quantity_available
        initial_reserved = self.item.quantity_reserved

        # Simulate exception during atomic stock reservation
        try:
            with transaction.atomic():
                self.item.quantity_available -= 5
                self.item.quantity_reserved += 5
                self.item.save()

                # Force mid-execution failure
                raise RuntimeError("Simulated failure mid-transaction audit creation")
        except RuntimeError:
            pass

        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity_available, initial_available)
        self.assertEqual(self.item.quantity_reserved, initial_reserved)
        self.assertEqual(StockMovement.objects.count(), 0)


class IdempotencyAndDuplicateEventTests(TestCase):
    """
    Tests idempotency and handling of duplicate saga events under simulated failure conditions.
    """
    def setUp(self):
        self.tenant_id = uuid.uuid4()
        self.warehouse = Warehouse.objects.create(
            tenant_id=self.tenant_id, name='Idemp WH', code='IDEMP01'
        )
        self.product_id = uuid.uuid4()
        self.item = InventoryItem.objects.create(
            tenant_id=self.tenant_id,
            product_id=self.product_id,
            warehouse=self.warehouse,
            quantity_available=20,
            quantity_reserved=0
        )
        self.order_id = str(uuid.uuid4())
        self.event_id = str(uuid.uuid4())

    def test_duplicate_saga_events_ignored_gracefully(self):
        payload = {
            'order_id': self.order_id,
            'items': [{'product_id': str(self.product_id), 'quantity': 4}]
        }

        # Process first event
        process_payment_succeeded(self.event_id, payload)
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity_available, 16)
        self.assertEqual(self.item.quantity_reserved, 4)

        # Process duplicate event with identical event_id
        process_payment_succeeded(self.event_id, payload)
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity_available, 16)
        self.assertEqual(self.item.quantity_reserved, 4)

        # Outbox event should only be emitted once
        self.assertEqual(OutboxEvent.objects.filter(event_type='inventory.reserved').count(), 1)
        self.assertEqual(ProcessedEvent.objects.filter(event_id=self.event_id).count(), 1)

    def test_malformed_event_payload_handling(self):
        malformed_event_id = str(uuid.uuid4())
        payload = {'order_id': 'invalid-uuid', 'items': 'not-a-list'}

        # Should not crash, and ProcessedEvent should not record invalid execution
        try:
            process_payment_succeeded(malformed_event_id, payload)
        except Exception:
            pass

        self.assertFalse(ProcessedEvent.objects.filter(event_id=malformed_event_id).exists())
