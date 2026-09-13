import time
import logging
from django.db import transaction
from .models import UserInteraction, ProductMetadataCache
from .neo4j_client import neo4j_client

logger = logging.getLogger(__name__)

WEIGHT_MAP = {
    'VIEW': 1.0,
    'LIKE': 2.0,
    'WISHLIST': 3.0,
    'CART': 4.0,
    'PURCHASE': 5.0,
    'REVIEW': 4.0,
}

def sync_event_to_graph(event_type, payload, event_id=None):
    """
    Idempotently sync an event to Postgres UserInteraction and Neo4j Graph DB.
    """
    if event_id:
        if UserInteraction.objects.filter(event_id=str(event_id)).exists():
            logger.info(f"Duplicate event {event_id} ignored.")
            return True

    current_ts = int(time.time())

    if event_type in ['order.paid', 'order.created']:
        user_id = payload.get('customer_id') or payload.get('user_id')
        tenant_id = payload.get('tenant_id')
        items = payload.get('items', [])
        
        if not user_id or not items:
            logger.warning(f"Missing user_id or items in {event_type} payload: {payload}")
            return False

        for item in items:
            product_id = item.get('product_id')
            if not product_id:
                continue

            try:
                UserInteraction.objects.create(
                    event_id=f"{event_id}_{product_id}" if event_id else None,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    product_id=product_id,
                    interaction_type='PURCHASE',
                    weight=WEIGHT_MAP['PURCHASE']
                )
            except Exception as e:
                logger.warning(f"Postgres interaction save error (purchased): {e}")

            try:
                meta, _ = ProductMetadataCache.objects.get_or_create(
                    product_id=product_id,
                    defaults={'name': f"Product {product_id[:8]}", 'tenant_id': tenant_id}
                )
                meta.purchase_count += item.get('quantity', 1)
                if tenant_id:
                    meta.tenant_id = tenant_id
                meta.save()
            except Exception as e:
                logger.warning(f"Product metadata update failed: {e}")

            cypher = """
            MERGE (u:User {id: $user_id})
            ON CREATE SET u.tenant_id = $tenant_id
            MERGE (p:Product {id: $product_id})
            ON CREATE SET p.tenant_id = $tenant_id
            MERGE (u)-[r:PURCHASED]->(p)
            ON CREATE SET r.count = $quantity, r.last_timestamp = $ts, r.weight = $weight
            ON MATCH SET r.count = coalesce(r.count, 0) + $quantity, r.last_timestamp = $ts
            """
            neo4j_client.execute_query(cypher, {
                'user_id': str(user_id),
                'product_id': str(product_id),
                'tenant_id': str(tenant_id) if tenant_id else '',
                'quantity': item.get('quantity', 1),
                'ts': current_ts,
                'weight': WEIGHT_MAP['PURCHASE']
            })

    elif event_type == 'cart.item_added':
        user_id = payload.get('user_id')
        tenant_id = payload.get('tenant_id')
        product_id = payload.get('product_id')
        quantity = payload.get('quantity', 1)

        if not user_id or not product_id:
            return False

        try:
            UserInteraction.objects.create(
                event_id=str(event_id) if event_id else None,
                tenant_id=tenant_id,
                user_id=user_id,
                product_id=product_id,
                interaction_type='CART',
                weight=WEIGHT_MAP['CART']
            )
        except Exception as e:
            logger.warning(f"Postgres interaction save error (cart): {e}")

        cypher = """
        MERGE (u:User {id: $user_id})
        ON CREATE SET u.tenant_id = $tenant_id
        MERGE (p:Product {id: $product_id})
        ON CREATE SET p.tenant_id = $tenant_id
        MERGE (u)-[r:ADDED_TO_CART]->(p)
        ON CREATE SET r.count = $quantity, r.last_timestamp = $ts, r.weight = $weight
        ON MATCH SET r.count = coalesce(r.count, 0) + $quantity, r.last_timestamp = $ts
        """
        neo4j_client.execute_query(cypher, {
            'user_id': str(user_id),
            'product_id': str(product_id),
            'tenant_id': str(tenant_id) if tenant_id else '',
            'quantity': int(quantity),
            'ts': current_ts,
            'weight': WEIGHT_MAP['CART']
        })

    elif event_type == 'wishlist.item_added':
        user_id = payload.get('user_id')
        tenant_id = payload.get('tenant_id')
        product_id = payload.get('product_id')

        if not user_id or not product_id:
            return False

        try:
            UserInteraction.objects.create(
                event_id=str(event_id) if event_id else None,
                tenant_id=tenant_id,
                user_id=user_id,
                product_id=product_id,
                interaction_type='WISHLIST',
                weight=WEIGHT_MAP['WISHLIST']
            )
        except Exception as e:
            logger.warning(f"Postgres interaction save error (wishlist): {e}")

        cypher = """
        MERGE (u:User {id: $user_id})
        ON CREATE SET u.tenant_id = $tenant_id
        MERGE (p:Product {id: $product_id})
        ON CREATE SET p.tenant_id = $tenant_id
        MERGE (u)-[r:ADDED_TO_WISHLIST]->(p)
        ON CREATE SET r.last_timestamp = $ts, r.weight = $weight
        ON MATCH SET r.last_timestamp = $ts
        """
        neo4j_client.execute_query(cypher, {
            'user_id': str(user_id),
            'product_id': str(product_id),
            'tenant_id': str(tenant_id) if tenant_id else '',
            'ts': current_ts,
            'weight': WEIGHT_MAP['WISHLIST']
        })

    elif event_type == 'product.liked':
        user_id = payload.get('user_id')
        tenant_id = payload.get('tenant_id')
        product_id = payload.get('product_id')

        if not user_id or not product_id:
            return False

        try:
            UserInteraction.objects.create(
                event_id=str(event_id) if event_id else None,
                tenant_id=tenant_id,
                user_id=user_id,
                product_id=product_id,
                interaction_type='LIKE',
                weight=WEIGHT_MAP['LIKE']
            )
        except Exception as e:
            logger.warning(f"Postgres interaction save error (like): {e}")

        cypher = """
        MERGE (u:User {id: $user_id})
        ON CREATE SET u.tenant_id = $tenant_id
        MERGE (p:Product {id: $product_id})
        ON CREATE SET p.tenant_id = $tenant_id
        MERGE (u)-[r:LIKED]->(p)
        ON CREATE SET r.last_timestamp = $ts, r.weight = $weight
        ON MATCH SET r.last_timestamp = $ts
        """
        neo4j_client.execute_query(cypher, {
            'user_id': str(user_id),
            'product_id': str(product_id),
            'tenant_id': str(tenant_id) if tenant_id else '',
            'ts': current_ts,
            'weight': WEIGHT_MAP['LIKE']
        })

    elif event_type == 'review.created':
        user_id = payload.get('user_id')
        tenant_id = payload.get('tenant_id')
        product_id = payload.get('product_id')
        rating = payload.get('rating', 5)

        if not user_id or not product_id:
            return False

        try:
            UserInteraction.objects.create(
                event_id=str(event_id) if event_id else None,
                tenant_id=tenant_id,
                user_id=user_id,
                product_id=product_id,
                interaction_type='REVIEW',
                weight=WEIGHT_MAP['REVIEW']
            )
        except Exception as e:
            logger.warning(f"Postgres interaction save error (review): {e}")

        cypher = """
        MERGE (u:User {id: $user_id})
        ON CREATE SET u.tenant_id = $tenant_id
        MERGE (p:Product {id: $product_id})
        ON CREATE SET p.tenant_id = $tenant_id
        MERGE (u)-[r:REVIEWED]->(p)
        ON CREATE SET r.rating = $rating, r.last_timestamp = $ts, r.weight = $weight
        ON MATCH SET r.rating = $rating, r.last_timestamp = $ts
        """
        neo4j_client.execute_query(cypher, {
            'user_id': str(user_id),
            'product_id': str(product_id),
            'tenant_id': str(tenant_id) if tenant_id else '',
            'rating': int(rating),
            'ts': current_ts,
            'weight': WEIGHT_MAP['REVIEW']
        })

    elif event_type in ['product.viewed', 'track-view']:
        user_id = payload.get('user_id')
        tenant_id = payload.get('tenant_id')
        product_id = payload.get('product_id')

        if not user_id or not product_id:
            return False

        try:
            UserInteraction.objects.create(
                event_id=str(event_id) if event_id else None,
                tenant_id=tenant_id,
                user_id=user_id,
                product_id=product_id,
                interaction_type='VIEW',
                weight=WEIGHT_MAP['VIEW']
            )
        except Exception as e:
            logger.warning(f"Postgres interaction save error (view): {e}")

        # Update view count in ProductMetadataCache
        try:
            meta, _ = ProductMetadataCache.objects.get_or_create(
                product_id=product_id,
                defaults={'name': f"Product {str(product_id)[:8]}", 'tenant_id': tenant_id}
            )
            meta.view_count += 1
            if tenant_id:
                meta.tenant_id = tenant_id
            meta.save()
        except Exception as e:
            logger.warning(f"Product metadata view count update failed: {e}")

        cypher = """
        MERGE (u:User {id: $user_id})
        ON CREATE SET u.tenant_id = $tenant_id
        MERGE (p:Product {id: $product_id})
        ON CREATE SET p.tenant_id = $tenant_id
        MERGE (u)-[r:VIEWED]->(p)
        ON CREATE SET r.count = 1, r.last_timestamp = $ts, r.weight = $weight
        ON MATCH SET r.count = coalesce(r.count, 0) + 1, r.last_timestamp = $ts
        """
        neo4j_client.execute_query(cypher, {
            'user_id': str(user_id),
            'product_id': str(product_id),
            'tenant_id': str(tenant_id) if tenant_id else '',
            'ts': current_ts,
            'weight': WEIGHT_MAP['VIEW']
        })

    elif event_type in ['product.created', 'product.updated', 'product.metadata']:
        product_id = payload.get('id') or payload.get('product_id')
        tenant_id = payload.get('tenant_id')
        name = payload.get('name', '')
        category_id = payload.get('category_id')
        category_name = payload.get('category_name', '')
        price = payload.get('price', 0.0)

        if not product_id:
            return False

        try:
            ProductMetadataCache.objects.update_or_create(
                product_id=product_id,
                defaults={
                    'tenant_id': tenant_id,
                    'name': name or f"Product {str(product_id)[:8]}",
                    'category_id': category_id,
                    'category_name': category_name,
                    'price': price or 0.0,
                }
            )
        except Exception as e:
            logger.warning(f"Failed to update ProductMetadataCache for {product_id}: {e}")

        cypher = """
        MERGE (p:Product {id: $product_id})
        SET p.tenant_id = $tenant_id, p.name = $name, p.category_id = $category_id
        """
        params = {
            'product_id': str(product_id),
            'tenant_id': str(tenant_id) if tenant_id else '',
            'name': str(name),
            'category_id': str(category_id) if category_id else '',
        }
        neo4j_client.execute_query(cypher, params)

        if category_id:
            cat_cypher = """
            MERGE (c:Category {id: $category_id})
            ON CREATE SET c.name = $category_name
            WITH c
            MATCH (p:Product {id: $product_id})
            MERGE (p)-[:BELONGS_TO]->(c)
            """
            neo4j_client.execute_query(cat_cypher, {
                'category_id': str(category_id),
                'category_name': str(category_name),
                'product_id': str(product_id),
            })

    return True
