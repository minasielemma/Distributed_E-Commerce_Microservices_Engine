import os
import json
import logging
import urllib.request
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .engine import (
    get_personalized_recommendations,
    get_copurchase_recommendations,
    get_similar_product_recommendations,
    get_trending_recommendations,
    get_recommended_merchants,
    get_recommended_categories
)
from .graph_sync import sync_event_to_graph
from .models import ProductMetadataCache, CachedRecommendation
from .serializers import TrackViewSerializer

logger = logging.getLogger(__name__)

# [Existing functions and classes omitted until end of file]
class RecommendedMerchantsView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        user_id = request.user.id if request.user and request.user.is_authenticated else None
        limit = int(request.query_params.get('limit', 10))
        merchants = get_recommended_merchants(user_id=user_id, limit=limit)
        return Response({'results': merchants}, status=status.HTTP_200_OK)


class RecommendedCategoriesView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        user_id = request.user.id if request.user and request.user.is_authenticated else None
        limit = int(request.query_params.get('limit', 10))
        categories = get_recommended_categories(user_id=user_id, limit=limit)
        return Response({'results': categories}, status=status.HTTP_200_OK)

def enrich_recommendations_with_catalog(recs, tenant_id=None):
    """
    Enriches recommendation items with full product details from catalog_service or ProductMetadataCache.
    """
    if not recs:
        return []

    product_ids = [r['product_id'] for r in recs if 'product_id' in r]
    if not product_ids:
        return recs

    catalog_map = {}

    # Try fetching from catalog_service via internal HTTP
    try:
        catalog_host = os.getenv('CATALOG_SERVICE_HOST', 'catalog_service')
        # Fetch products from catalog_service
        # We can bulk fetch or query catalog API
        for pid in product_ids[:20]:
            try:
                url = f"http://{catalog_host}:8000/api/catalog/products/{pid}/"
                req = urllib.request.Request(url, headers={'Content-Type': 'application/json'})
                with urllib.request.urlopen(req, timeout=1.5) as resp:
                    if resp.status == 200:
                        prod_data = json.loads(resp.read().decode())
                        catalog_map[str(pid)] = prod_data
            except Exception:
                pass
    except Exception as e:
        logger.warning(f"Failed to fetch catalog product details: {e}")

    # For any missing products, fallback to ProductMetadataCache
    missing_ids = [pid for pid in product_ids if str(pid) not in catalog_map]
    if missing_ids:
        cache_qs = ProductMetadataCache.objects.filter(product_id__in=missing_ids)
        for meta in cache_qs:
            catalog_map[str(meta.product_id)] = {
                'id': str(meta.product_id),
                'name': meta.name,
                'price': float(meta.price),
                'base_price': float(meta.price),
                'category_name': meta.category_name,
                'rating_avg': meta.rating_avg,
                'images': []
            }

    enriched = []
    for rec in recs:
        pid_str = str(rec['product_id'])
        prod = catalog_map.get(pid_str)
        if prod:
            item = dict(prod)
            item['recommendation_score'] = rec.get('score', 1.0)
            item['recommendation_reason'] = rec.get('reason', '')
            enriched.append(item)
        else:
            # Fallback stub object if product not in catalog or cache
            enriched.append({
                'id': pid_str,
                'name': f"Product {pid_str[:8]}",
                'price': 0.0,
                'base_price': 0.0,
                'recommendation_score': rec.get('score', 1.0),
                'recommendation_reason': rec.get('reason', '')
            })

    return enriched


class PersonalizedRecommendationsView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        user_id = request.user.id if request.user and request.user.is_authenticated else None
        header_tenant = request.headers.get('X-Tenant-Id') or request.headers.get('X-Tenant-ID')
        tenant_id = getattr(request.user, 'tenant_id', None) or header_tenant or request.query_params.get('tenant_id')
        limit = int(request.query_params.get('limit', 10))

        if user_id:
            recs = get_personalized_recommendations(user_id=user_id, tenant_id=tenant_id, limit=limit)
        else:
            recs = get_trending_recommendations(tenant_id=tenant_id, limit=limit)

        enriched = enrich_recommendations_with_catalog(recs, tenant_id=tenant_id)
        return Response({
            'recommendation_type': 'PERSONALIZED' if user_id else 'TRENDING',
            'user_id': str(user_id) if user_id else None,
            'results': enriched
        }, status=status.HTTP_200_OK)


class CopurchaseRecommendationsView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        product_id = request.query_params.get('product_id')
        if not product_id:
            return Response({'error': 'product_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

        header_tenant = request.headers.get('X-Tenant-Id') or request.headers.get('X-Tenant-ID')
        tenant_id = getattr(request.user, 'tenant_id', None) or header_tenant or request.query_params.get('tenant_id')
        limit = int(request.query_params.get('limit', 10))

        recs = get_copurchase_recommendations(product_id=product_id, tenant_id=tenant_id, limit=limit)
        enriched = enrich_recommendations_with_catalog(recs, tenant_id=tenant_id)
        return Response({
            'recommendation_type': 'CO_PURCHASE',
            'source_product_id': str(product_id),
            'results': enriched
        }, status=status.HTTP_200_OK)


class SimilarRecommendationsView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        product_id = request.query_params.get('product_id')
        if not product_id:
            return Response({'error': 'product_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

        header_tenant = request.headers.get('X-Tenant-Id') or request.headers.get('X-Tenant-ID')
        tenant_id = getattr(request.user, 'tenant_id', None) or header_tenant or request.query_params.get('tenant_id')
        limit = int(request.query_params.get('limit', 10))

        recs = get_similar_product_recommendations(product_id=product_id, tenant_id=tenant_id, limit=limit)
        enriched = enrich_recommendations_with_catalog(recs, tenant_id=tenant_id)
        return Response({
            'recommendation_type': 'SIMILAR',
            'source_product_id': str(product_id),
            'results': enriched
        }, status=status.HTTP_200_OK)


class TrendingRecommendationsView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        header_tenant = request.headers.get('X-Tenant-Id') or request.headers.get('X-Tenant-ID')
        tenant_id = getattr(request.user, 'tenant_id', None) or header_tenant or request.query_params.get('tenant_id')
        limit = int(request.query_params.get('limit', 10))

        recs = get_trending_recommendations(tenant_id=tenant_id, limit=limit)
        enriched = enrich_recommendations_with_catalog(recs, tenant_id=tenant_id)
        return Response({
            'recommendation_type': 'TRENDING',
            'results': enriched
        }, status=status.HTTP_200_OK)


class TrackViewApiView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = TrackViewSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        product_id = serializer.validated_data['product_id']
        tenant_id = serializer.validated_data.get('tenant_id') or request.headers.get('X-Tenant-Id') or request.headers.get('X-Tenant-ID')
        user_id = request.user.id if request.user and request.user.is_authenticated else None

        if not user_id:
            # Anonymous view tracking
            user_id = request.data.get('anonymous_id') or '00000000-0000-0000-0000-000000000000'

        payload = {
            'user_id': str(user_id),
            'product_id': str(product_id),
            'tenant_id': str(tenant_id) if tenant_id else None
        }

        # Sync asynchronously or inline
        try:
            sync_event_to_graph(event_type='track-view', payload=payload)
        except Exception as e:
            logger.error(f"Track view sync error: {e}")

        return Response({'status': 'view tracked'}, status=status.HTTP_200_OK)
