import os
import json
import logging
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
from .grpc_client import get_catalog_product_grpc

logger = logging.getLogger(__name__)


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

import requests

def _fetch_catalog_product_http(pid):
    try:
        url = f"http://catalog-service:8000/api/catalog/products/{pid}/"
        resp = requests.get(url, timeout=3)
        if resp.status_code == 200:
            return resp.json()
    except Exception as err:
        logger.warning(f"HTTP fallback fetch for product {pid} failed: {err}")
    return None

def enrich_recommendations_with_catalog(recs, tenant_id=None):
    """
    Enriches recommendation items with full product details including image URLs from catalog_service.
    """
    if not recs:
        return []

    product_ids = [r['product_id'] for r in recs if 'product_id' in r]
    if not product_ids:
        return recs

    catalog_map = {}

    # Fetch from catalog_service via HTTP REST or gRPC
    for pid in product_ids[:20]:
        prod_data = _fetch_catalog_product_http(pid)
        if prod_data:
            name = prod_data.get('name') or prod_data.get('title') or f"Product {str(pid)[:8]}"
            price = float(prod_data.get('dynamic_price') or prod_data.get('base_price') or prod_data.get('price') or 0.0)
            img_url = prod_data.get('image_url') or (prod_data.get('images', [{}])[0].get('image_url') if prod_data.get('images') else '') or ''
            images = prod_data.get('images') or ([{'image_url': img_url}] if img_url else [])
            catalog_map[str(pid)] = {
                'id': str(pid),
                'name': name,
                'price': price,
                'base_price': price,
                'category_name': prod_data.get('category_name', ''),
                'rating_avg': float(prod_data.get('average_rating') or prod_data.get('rating_avg') or 0.0),
                'image_url': img_url,
                'images': images
            }
        else:
            try:
                prod_pb = get_catalog_product_grpc(pid)
                if prod_pb and getattr(prod_pb, 'found', False) and prod_pb.id:
                    title = getattr(prod_pb, 'title', '') or getattr(prod_pb, 'name', '')
                    price = float(getattr(prod_pb, 'price', 0.0))
                    img_url = getattr(prod_pb, 'image_url', '') or ''
                    catalog_map[str(pid)] = {
                        'id': str(prod_pb.id),
                        'name': title,
                        'price': price,
                        'base_price': price,
                        'category_name': getattr(prod_pb, 'category_name', ''),
                        'rating_avg': getattr(prod_pb, 'rating_avg', 0.0),
                        'image_url': img_url,
                        'images': [{'image_url': img_url}] if img_url else []
                    }
            except Exception as e:
                logger.warning(f"Failed to fetch catalog product details via gRPC for {pid}: {e}")

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
                'image_url': getattr(meta, 'image_url', ''),
                'images': [{'image_url': getattr(meta, 'image_url', '')}] if getattr(meta, 'image_url', '') else []
            }

    enriched = []
    default_fallback_img = 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&auto=format&fit=crop&q=80'
    for rec in recs:
        pid_str = str(rec['product_id'])
        prod = catalog_map.get(pid_str)
        if prod:
            item = dict(prod)
            item['recommendation_score'] = rec.get('score', 1.0)
            item['recommendation_reason'] = rec.get('reason', '')
            if not item.get('image_url') and item.get('images'):
                item['image_url'] = item['images'][0].get('image_url')
            if not item.get('image_url'):
                item['image_url'] = default_fallback_img
                item['images'] = [{'image_url': default_fallback_img}]
            enriched.append(item)
        else:
            enriched.append({
                'id': pid_str,
                'name': f"Product {pid_str[:8]}",
                'price': 0.0,
                'base_price': 0.0,
                'image_url': default_fallback_img,
                'images': [{'image_url': default_fallback_img}],
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
