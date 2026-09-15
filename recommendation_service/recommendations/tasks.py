import logging
from celery import shared_task
from .models import UserInteraction, ProductMetadataCache, CachedRecommendation
from .engine import get_personalized_recommendations, get_trending_recommendations
from .grpc_client import list_catalog_products_grpc

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
    Periodic task to sync product metadata from catalog_service into ProductMetadataCache via gRPC.
    """
    logger.info("Starting product metadata sync from catalog_service via gRPC...")
    try:
        results = list_catalog_products_grpc(page=1, page_size=100)
        for prod in results:
            pid = prod.id
            if pid:
                ProductMetadataCache.objects.update_or_create(
                    product_id=pid,
                    defaults={
                        'tenant_id': prod.tenant_id,
                        'name': prod.name,
                        'category_id': prod.category,
                        'category_name': prod.category_name,
                        'price': prod.base_price,
                        'rating_avg': prod.rating_avg,
                    }
                )
        return f"Synced {len(results)} products to ProductMetadataCache."
    except Exception as e:
        logger.error(f"Failed product metadata sync: {e}")
        return f"Failed sync: {e}"

