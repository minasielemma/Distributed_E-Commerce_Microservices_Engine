import uuid
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from inventory.models import Warehouse, InventoryItem, StockMovement, OutboxEvent, ProcessedEvent
from inventory.saga_consumer import process_payment_succeeded, process_stock_release


def make_user_with_tenant():
    from django.contrib.auth.models import User
    user = User.objects.create_user(username=f'invuser_{uuid.uuid4().hex[:6]}', password='pass123')
    tenant_id = uuid.uuid4()
    user.tenant_id = tenant_id
    return user, tenant_id


class WarehouseViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user, self.tenant_id = make_user_with_tenant()
        self.client.force_authenticate(user=self.user)

    def test_create_warehouse(self):
        data = {'name': 'Main Warehouse', 'code': 'WH001', 'address': '123 Main St'}
        response = self.client.post('/api/inventory/warehouses/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Warehouse.objects.filter(code='WH001', tenant_id=self.tenant_id).exists())

    def test_list_warehouses_scoped_to_tenant(self):
        Warehouse.objects.create(tenant_id=self.tenant_id, name='WH A', code='WHA')
        Warehouse.objects.create(tenant_id=uuid.uuid4(), name='WH B', code='WHB')
        response = self.client.get('/api/inventory/warehouses/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1)

    def test_list_warehouses_no_tenant_returns_empty(self):
        from django.contrib.auth.models import User
        user_no_tenant = User.objects.create_user(username='notenant', password='pass123')
        self.client.force_authenticate(user=user_no_tenant)
        Warehouse.objects.create(tenant_id=uuid.uuid4(), name='WH', code='WH1')
        response = self.client.get('/api/inventory/warehouses/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 0)

    def test_unauthenticated_warehouse_access_fails(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/inventory/warehouses/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_warehouse(self):
        wh = Warehouse.objects.create(tenant_id=self.tenant_id, name='Del WH', code='DELWH')
        response = self.client.delete(f'/api/inventory/warehouses/{wh.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class InventoryItemViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user, self.tenant_id = make_user_with_tenant()
        self.client.force_authenticate(user=self.user)
        self.warehouse = Warehouse.objects.create(tenant_id=self.tenant_id, name='WH', code='WH01')

    def test_create_inventory_item(self):
        data = {
            'product_id': str(uuid.uuid4()),
            'warehouse': str(self.warehouse.id),
            'quantity_available': 50,
            'quantity_reserved': 0,
            'reorder_level': 10
        }
        response = self.client.post('/api/inventory/items/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(InventoryItem.objects.filter(tenant_id=self.tenant_id).count(), 1)

    def test_list_items_scoped_to_tenant(self):
        other_wh = Warehouse.objects.create(tenant_id=uuid.uuid4(), name='Other', code='OTH')
        InventoryItem.objects.create(tenant_id=self.tenant_id, product_id=uuid.uuid4(),
                                     warehouse=self.warehouse, quantity_available=10)
        InventoryItem.objects.create(tenant_id=uuid.uuid4(), product_id=uuid.uuid4(),
                                     warehouse=other_wh, quantity_available=5)
        response = self.client.get('/api/inventory/items/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1)

    def test_unauthenticated_item_access_fails(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/inventory/items/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ReserveStockViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user, self.tenant_id = make_user_with_tenant()
        self.client.force_authenticate(user=self.user)
        self.warehouse = Warehouse.objects.create(tenant_id=self.tenant_id, name='WH', code='WH02')
        self.product_id = uuid.uuid4()
        self.item = InventoryItem.objects.create(
            tenant_id=self.tenant_id, product_id=self.product_id,
            warehouse=self.warehouse, quantity_available=20, quantity_reserved=0
        )

    def test_reserve_stock_success(self):
        data = {'product_id': str(self.product_id), 'quantity': 5, 'reference_id': 'order-123'}
        response = self.client.post('/api/inventory/reserve/', data, HTTP_X_SERVICE_TOKEN='internal-token')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity_available, 15)
        self.assertEqual(self.item.quantity_reserved, 5)

    def test_reserve_stock_creates_movement(self):
        data = {'product_id': str(self.product_id), 'quantity': 3}
        self.client.post('/api/inventory/reserve/', data, HTTP_X_SERVICE_TOKEN='internal-token')
        self.assertTrue(StockMovement.objects.filter(
            inventory_item=self.item, movement_type='RESERVED', quantity=3
        ).exists())

    def test_release_stock_success(self):
        self.item.quantity_available = 15
        self.item.quantity_reserved = 5
        self.item.save()
        data = {'product_id': str(self.product_id), 'quantity': 5}
        response = self.client.post('/api/inventory/release/', data, HTTP_X_SERVICE_TOKEN='internal-token')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity_available, 20)
        self.assertEqual(self.item.quantity_reserved, 0)


class InventorySagaTests(TestCase):
    def setUp(self):
        self.tenant_id = uuid.uuid4()
        self.warehouse = Warehouse.objects.create(tenant_id=self.tenant_id, name='Saga WH', code='SAGA01')
        self.product_id = uuid.uuid4()
        self.item = InventoryItem.objects.create(
            tenant_id=self.tenant_id, product_id=self.product_id,
            warehouse=self.warehouse, quantity_available=10, quantity_reserved=0
        )
        self.order_id = str(uuid.uuid4())
        self.event_id = str(uuid.uuid4())

    def test_payment_succeeded_reserves_stock_and_creates_outbox_event(self):
        payload = {
            'order_id': self.order_id,
            'items': [{'product_id': str(self.product_id), 'quantity': 2}]
        }
        process_payment_succeeded(self.event_id, payload)

        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity_available, 8)
        self.assertEqual(self.item.quantity_reserved, 2)
        self.assertTrue(OutboxEvent.objects.filter(event_type='inventory.reserved').exists())
        self.assertTrue(ProcessedEvent.objects.filter(event_id=self.event_id).exists())

    def test_idempotent_processing_prevents_duplicate_reservations(self):
        payload = {
            'order_id': self.order_id,
            'items': [{'product_id': str(self.product_id), 'quantity': 2}]
        }
        process_payment_succeeded(self.event_id, payload)
        process_payment_succeeded(self.event_id, payload)

        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity_available, 8)
        self.assertEqual(self.item.quantity_reserved, 2)
        self.assertEqual(ProcessedEvent.objects.filter(event_id=self.event_id).count(), 1)

    def test_stock_release_compensating_transaction(self):
        payload = {
            'order_id': self.order_id,
            'items': [{'product_id': str(self.product_id), 'quantity': 3}]
        }
        process_payment_succeeded(self.event_id, payload)

        release_event_id = str(uuid.uuid4())
        release_payload = {'order_id': self.order_id}
        process_stock_release(release_event_id, release_payload)

        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity_available, 10)
        self.assertEqual(self.item.quantity_reserved, 0)
        self.assertTrue(OutboxEvent.objects.filter(event_type='inventory.released').exists())
