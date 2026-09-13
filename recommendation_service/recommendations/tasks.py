import os
import json
import logging
import urllib.request
from celery import shared_task
from .models import UserInteraction, ProductMetadataCache, CachedRecommendation
from .engine import get_personalized_recommendations, get_trending_recommendations

logger = logging.getLogger(__name__)

@shared_task
def precompute_recommendations():
    """
    Precompute personalized and trending recommendations for active users.
    """
    logger.info("Starting background precomputation of recommendations...")
    active_user_ids = UserInteraction.objects.values_list('user_id', flat=True).distinct()[:500]

    count = 0
    for uid in active_user_ids:
        try:
            recs = get_personalized_recommendations(user_id=uid, limit=10)
            CachedRecommendation.objects.update_or_create(
                user_id=uid,
                recommendation_type='PERSONALIZED',
                source_product_id=None,
                defaults={'recommendations_json': recs}
            )
            count += 1
        except Exception as e:
            logger.error(f"Error precomputing for user {uid}: {e}")

    try:
        trending = get_trending_recommendations(limit=10)
        CachedRecommendation.objects.update_or_create(
            user_id=None,
            recommendation_type='TRENDING',
            source_product_id=None,
            defaults={'recommendations_json': trending}
        )
    except Exception as e:
        logger.error(f"Error precomputing trending recommendations: {e}")

    return f"Precomputed recommendations for {count} users."


@shared_task
def sync_product_metadata():
    """
    Periodic task to sync product metadata from catalog_service into ProductMetadataCache.
    """
    logger.info("Starting product metadata sync from catalog_service...")
    try:
        catalog_host = os.getenv('CATALOG_SERVICE_HOST', 'catalog_service')
        url = f"http://{catalog_host}:8000/api/catalog/products/?page_size=100"
        req = urllib.request.Request(url, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode())
                results = data.get('results', [])
                for prod in results:
                    pid = prod.get('id')
                    if pid:
                        ProductMetadataCache.objects.update_or_create(
                            product_id=pid,
                            defaults={
                                'tenant_id': prod.get('tenant_id'),
                                'name': prod.get('name', ''),
                                'category_id': prod.get('category'),
                                'category_name': prod.get('category_name', ''),
                                'price': prod.get('base_price', 0.0),
                                'rating_avg': prod.get('rating_avg', 0.0),
                            }
                        )
                return f"Synced {len(results)} products to ProductMetadataCache."
    except Exception as e:
        logger.error(f"Failed product metadata sync: {e}")
        return f"Failed sync: {e}"
