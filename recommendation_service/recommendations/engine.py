import math
import time
import logging
from django.db.models import Count, Q
from .models import UserInteraction, ProductMetadataCache, CachedRecommendation
from .neo4j_client import neo4j_client

logger = logging.getLogger(__name__)

def get_personalized_recommendations(user_id, tenant_id=None, limit=10):
    """
    Generate personalized product recommendations for a user.
    Uses Collaborative Filtering (CF) + Content-Based Filtering (CBF) via Neo4j,
    falling back to popular/trending products in Postgres if Neo4j yields insufficient results.
    """
    recommendations = []
    seen_product_ids = set()

    cf_cypher = """
    MATCH (u:User {id: $user_id})-[r1:VIEWED|ADDED_TO_CART|PURCHASED|LIKED|ADDED_TO_WISHLIST]->(p1:Product)
    MATCH (other:User)-[r2:VIEWED|ADDED_TO_CART|PURCHASED|LIKED|ADDED_TO_WISHLIST]->(p1)
    WHERE other <> u
    MATCH (other)-[r3:VIEWED|ADDED_TO_CART|PURCHASED|LIKED|ADDED_TO_WISHLIST]->(p2:Product)
    WHERE NOT (u)-[:PURCHASED]->(p2) AND p2 <> p1
    """
    if tenant_id:
        cf_cypher += " AND (p2.tenant_id = $tenant_id OR p2.tenant_id IS NULL OR p2.tenant_id = '')"

    cf_cypher += """
    RETURN p2.id AS product_id, sum(r3.weight) AS score
    ORDER BY score DESC
    LIMIT $limit
    """

    try:
        neo_results = neo4j_client.execute_query(cf_cypher, {
            'user_id': str(user_id),
            'tenant_id': str(tenant_id) if tenant_id else '',
            'limit': limit * 2
        })
        for rec in neo_results:
            pid = rec.get('product_id')
            if pid and pid not in seen_product_ids:
                seen_product_ids.add(pid)
                recommendations.append({'product_id': pid, 'score': float(rec.get('score', 1.0)), 'reason': 'Based on your history and similar shoppers'})
    except Exception as e:
        logger.error(f"CF Neo4j query error: {e}")

    if len(recommendations) < limit:
        cbf_cypher = """
        MATCH (u:User {id: $user_id})-[r:VIEWED|ADDED_TO_CART|PURCHASED|LIKED]->(p:Product)-[:BELONGS_TO]->(c:Category)
        MATCH (c)<-[:BELONGS_TO]-(p2:Product)
        WHERE NOT (u)-[:PURCHASED]->(p2)
        """
        if tenant_id:
            cbf_cypher += " AND (p2.tenant_id = $tenant_id OR p2.tenant_id IS NULL OR p2.tenant_id = '')"

        cbf_cypher += """
        RETURN p2.id AS product_id, count(p) AS score
        ORDER BY score DESC
        LIMIT $limit
        """
        try:
            cbf_results = neo4j_client.execute_query(cbf_cypher, {
                'user_id': str(user_id),
                'tenant_id': str(tenant_id) if tenant_id else '',
                'limit': limit
            })
            for rec in cbf_results:
                pid = rec.get('product_id')
                if pid and pid not in seen_product_ids:
                    seen_product_ids.add(pid)
                    recommendations.append({'product_id': pid, 'score': float(rec.get('score', 1.0)), 'reason': 'Similar to items you viewed'})
        except Exception as e:
            logger.error(f"CBF Neo4j query error: {e}")

    if len(recommendations) < limit:
        needed = limit - len(recommendations)
        qs = ProductMetadataCache.objects.all()
        if tenant_id:
            qs = qs.filter(Q(tenant_id=tenant_id) | Q(tenant_id__isnull=True))
        
        fallback_prods = qs.exclude(product_id__in=seen_product_ids).order_by('-purchase_count', '-view_count')[:needed]
        for prod in fallback_prods:
            pid = str(prod.product_id)
            seen_product_ids.add(pid)
            recommendations.append({'product_id': pid, 'score': 0.5, 'reason': 'Popular in store'})

    return recommendations[:limit]


def get_copurchase_recommendations(product_id, tenant_id=None, limit=10):
    """
    Generate 'Frequently Bought Together' recommendations for a given product.
    """
    recommendations = []
    seen = set()

    cypher = """
    MATCH (p1:Product {id: $product_id})<-[r1:PURCHASED]-(u:User)-[r2:PURCHASED]->(p2:Product)
    WHERE p1 <> p2
    """
    if tenant_id:
        cypher += " AND (p2.tenant_id = $tenant_id OR p2.tenant_id IS NULL OR p2.tenant_id = '')"

    cypher += """
    RETURN p2.id AS product_id, count(u) AS copurchase_count
    ORDER BY copurchase_count DESC
    LIMIT $limit
    """

    try:
        results = neo4j_client.execute_query(cypher, {
            'product_id': str(product_id),
            'tenant_id': str(tenant_id) if tenant_id else '',
            'limit': limit
        })
        for rec in results:
            pid = rec.get('product_id')
            if pid and pid not in seen:
                seen.add(pid)
                recommendations.append({'product_id': pid, 'score': float(rec.get('copurchase_count', 1)), 'reason': 'Frequently bought together'})
    except Exception as e:
        logger.error(f"Co-purchase Neo4j query error: {e}")

    if len(recommendations) < limit:
        target_meta = ProductMetadataCache.objects.filter(product_id=product_id).first()
        qs = ProductMetadataCache.objects.exclude(product_id=product_id)
        if tenant_id:
            qs = qs.filter(Q(tenant_id=tenant_id) | Q(tenant_id__isnull=True))

        if target_meta and target_meta.category_id:
            qs = qs.filter(category_id=target_meta.category_id)

        fallback_prods = qs.exclude(product_id__in=seen).order_by('-purchase_count')[:limit - len(recommendations)]
        for prod in fallback_prods:
            pid = str(prod.product_id)
            seen.add(pid)
            recommendations.append({'product_id': pid, 'score': 0.3, 'reason': 'Similar product'})

    return recommendations[:limit]


def get_similar_product_recommendations(product_id, tenant_id=None, limit=10):
    """
    Generate 'Similar Products' recommendations based on category + interaction co-occurrence.
    """
    recommendations = []
    seen = set()

    cypher = """
    MATCH (p1:Product {id: $product_id})-[:BELONGS_TO]->(c:Category)<-[:BELONGS_TO]-(p2:Product)
    WHERE p1 <> p2
    """
    if tenant_id:
        cypher += " AND (p2.tenant_id = $tenant_id OR p2.tenant_id IS NULL OR p2.tenant_id = '')"

    cypher += """
    OPTIONAL MATCH (p1)<-[r1:VIEWED|LIKED|ADDED_TO_CART]-(u:User)-[r2:VIEWED|LIKED|ADDED_TO_CART]->(p2)
    RETURN p2.id AS product_id, count(u) + 1 AS score
    ORDER BY score DESC
    LIMIT $limit
    """

    try:
        results = neo4j_client.execute_query(cypher, {
            'product_id': str(product_id),
            'tenant_id': str(tenant_id) if tenant_id else '',
            'limit': limit
        })
        for rec in results:
            pid = rec.get('product_id')
            if pid and pid not in seen:
                seen.add(pid)
                recommendations.append({'product_id': pid, 'score': float(rec.get('score', 1)), 'reason': 'Similar category & views'})
    except Exception as e:
        logger.error(f"Similar product Neo4j query error: {e}")

    if len(recommendations) < limit:
        target_meta = ProductMetadataCache.objects.filter(product_id=product_id).first()
        qs = ProductMetadataCache.objects.exclude(product_id=product_id)
        if tenant_id:
            qs = qs.filter(Q(tenant_id=tenant_id) | Q(tenant_id__isnull=True))

        if target_meta and target_meta.category_id:
            qs = qs.filter(category_id=target_meta.category_id)

        fallback_prods = qs.exclude(product_id__in=seen).order_by('-view_count', '-purchase_count')[:limit - len(recommendations)]
        for prod in fallback_prods:
            pid = str(prod.product_id)
            seen.add(pid)
            recommendations.append({'product_id': pid, 'score': 0.4, 'reason': 'Popular in category'})

    return recommendations[:limit]


def get_trending_recommendations(tenant_id=None, limit=10):
    """
    Generate 'Trending Products' recommendations based on recent interaction volume in Postgres/Neo4j.
    """
    recommendations = []
    seen = set()

    try:
        qs = UserInteraction.objects.all()
        if tenant_id:
            qs = qs.filter(Q(tenant_id=tenant_id) | Q(tenant_id__isnull=True))

        trending_counts = (
            qs.values('product_id')
            .annotate(interaction_score=Count('id'))
            .order_by('-interaction_score')[:limit]
        )

        for item in trending_counts:
            pid = str(item['product_id'])
            seen.add(pid)
            recommendations.append({
                'product_id': pid,
                'score': float(item['interaction_score']),
                'reason': 'Trending now'
            })
    except Exception as e:
        logger.error(f"Trending Postgres error: {e}")

    if len(recommendations) < limit:
        needed = limit - len(recommendations)
        qs = ProductMetadataCache.objects.all()
        if tenant_id:
            qs = qs.filter(Q(tenant_id=tenant_id) | Q(tenant_id__isnull=True))

        fallback_prods = qs.exclude(product_id__in=seen).order_by('-purchase_count', '-view_count')[:needed]
        for prod in fallback_prods:
            pid = str(prod.product_id)
            seen.add(pid)
            recommendations.append({'product_id': pid, 'score': 1.0, 'reason': 'Top selling'})

    return recommendations[:limit]

def get_recommended_merchants(user_id=None, limit=10):
    """
    Returns top recommended merchants for a user based on interactions or global activity.
    """
    merchants = []
    if user_id:
        try:
            cypher = """
            MATCH (u:User {id: $user_id})-[r:VIEWED|ADDED_TO_CART|PURCHASED]->(p:Product)
            WHERE p.tenant_id IS NOT NULL AND p.tenant_id <> ''
            RETURN p.tenant_id AS tenant_id, count(r) AS score
            ORDER BY score DESC
            LIMIT $limit
            """
            neo_results = neo4j_client.execute_query(cypher, {'user_id': str(user_id), 'limit': limit})
            for r in neo_results:
                if r.get('tenant_id'):
                    merchants.append({'tenant_id': r['tenant_id'], 'score': float(r.get('score', 1.0))})
        except Exception as e:
            logger.error(f"Merchant recommendation Neo4j query error: {e}")

    if len(merchants) < limit:
        existing_ids = {m['tenant_id'] for m in merchants}
        qs = UserInteraction.objects.values('tenant_id').annotate(score=Count('id')).filter(tenant_id__isnull=False).order_by('-score')
        for item in qs:
            tid = str(item['tenant_id'])
            if tid and tid not in existing_ids:
                existing_ids.add(tid)
                merchants.append({'tenant_id': tid, 'score': float(item['score'])})
                if len(merchants) >= limit:
                    break

    return merchants

def get_recommended_categories(user_id=None, limit=10):
    """
    Returns top recommended categories for a user based on interactions.
    """
    categories = []
    if user_id:
        try:
            cypher = """
            MATCH (u:User {id: $user_id})-[r:VIEWED|ADDED_TO_CART|PURCHASED]->(p:Product)-[:BELONGS_TO]->(c:Category)
            RETURN c.id AS category_id, c.name AS category_name, count(r) AS score
            ORDER BY score DESC
            LIMIT $limit
            """
            neo_results = neo4j_client.execute_query(cypher, {'user_id': str(user_id), 'limit': limit})
            for r in neo_results:
                if r.get('category_id'):
                    categories.append({'category_id': r['category_id'], 'category_name': r.get('category_name'), 'score': float(r.get('score', 1.0))})
        except Exception as e:
            logger.error(f"Category recommendation Neo4j query error: {e}")

    if len(categories) < limit:
        existing_ids = {c.get('category_id') for c in categories if c.get('category_id')}
        cache_qs = ProductMetadataCache.objects.values('category_name').annotate(score=Count('id')).order_by('-score')
        for item in cache_qs:
            cname = item['category_name']
            if cname and cname not in existing_ids:
                existing_ids.add(cname)
                categories.append({'category_name': cname, 'score': float(item['score'])})
                if len(categories) >= limit:
                    break

    return categories
