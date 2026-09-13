import uuid
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import UserInteraction, ProductMetadataCache, CachedRecommendation
from .graph_sync import sync_event_to_graph
from .engine import (
    get_personalized_recommendations,
    get_copurchase_recommendations,
    get_similar_product_recommendations,
    get_trending_recommendations
)

class RecommendationSystemTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_id = uuid.uuid4()
        self.tenant_id = uuid.uuid4()
        self.product_id_1 = uuid.uuid4()
        self.product_id_2 = uuid.uuid4()

        # Populate test metadata cache
        self.meta1 = ProductMetadataCache.objects.create(
            product_id=self.product_id_1,
            tenant_id=self.tenant_id,
            name="Test Phone",
            price=499.99,
            purchase_count=10,
            view_count=50
        )
        self.meta2 = ProductMetadataCache.objects.create(
            product_id=self.product_id_2,
            tenant_id=self.tenant_id,
            name="Phone Case",
            price=19.99,
            purchase_count=8,
            view_count=30
        )

    def test_track_view_endpoint(self):
        url = reverse('recommendations-track-view')
        data = {
            'product_id': str(self.product_id_1),
            'tenant_id': str(self.tenant_id)
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'view tracked')

        # Check Postgres UserInteraction recorded
        self.assertTrue(UserInteraction.objects.filter(product_id=self.product_id_1, interaction_type='VIEW').exists())

    def test_trending_recommendations_endpoint(self):
        url = reverse('recommendations-trending')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_copurchase_recommendations_endpoint(self):
        url = f"{reverse('recommendations-copurchase')}?product_id={self.product_id_1}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['source_product_id'], str(self.product_id_1))

    def test_similar_recommendations_endpoint(self):
        url = f"{reverse('recommendations-similar')}?product_id={self.product_id_1}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['source_product_id'], str(self.product_id_1))

    def test_idempotent_event_processing(self):
        event_id = "evt-test-12345"
        payload = {
            'user_id': str(self.user_id),
            'product_id': str(self.product_id_1),
            'tenant_id': str(self.tenant_id)
        }
        # First sync
        res1 = sync_event_to_graph('cart.item_added', payload, event_id=event_id)
        self.assertTrue(res1)
        initial_count = UserInteraction.objects.filter(event_id=event_id).count()
        self.assertEqual(initial_count, 1)

        # Duplicate sync with same event_id
        res2 = sync_event_to_graph('cart.item_added', payload, event_id=event_id)
        self.assertTrue(res2)
        second_count = UserInteraction.objects.filter(event_id=event_id).count()
        self.assertEqual(second_count, 1)  # No duplicate created

    @patch('recommendations.engine.neo4j_client.execute_query')
    def test_engine_fallback_when_neo4j_empty(self, mock_neo):
        mock_neo.return_value = []
        recs = get_personalized_recommendations(user_id=self.user_id, tenant_id=self.tenant_id, limit=5)
        # Should fallback to ProductMetadataCache and return items
        self.assertGreaterEqual(len(recs), 1)
        self.assertIn('product_id', recs[0])
