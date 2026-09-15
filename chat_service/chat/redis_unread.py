import os
import logging
import redis
from django.core.cache import cache

logger = logging.getLogger(__name__)

def get_redis_client():
    try:
        if hasattr(cache, '_cache') and hasattr(cache._cache, 'get_client'):
            return cache._cache.get_client()
        if hasattr(cache, 'client') and hasattr(cache.client, 'get_client'):
            return cache.client.get_client()
        if hasattr(cache, 'get_client'):
            return cache.get_client()
    except Exception as e:
        logger.warning(f"Failed to retrieve Redis client from Django cache settings: {e}")

    try:
        redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
        return redis.Redis.from_url(redis_url, decode_responses=True)
    except Exception as ex:
        logger.warning(f"Fallback Redis connection failed: {ex}")
        return None

def get_unread_key(user_id):
    return f"unread:user:{user_id}"

def get_user_room_unread(user_id, room_id):
    r = get_redis_client()
    if not r:
        return None
    try:
        key = get_unread_key(user_id)
        if not r.exists(key):
            return warmup_user_unread_cache(user_id).get(str(room_id), 0)
        val = r.hget(key, str(room_id))
        return int(val) if val is not None else 0
    except Exception as e:
        logger.warning(f"Redis get_user_room_unread error for {user_id}: {e}")
        return None

def get_user_total_unread(user_id):
    r = get_redis_client()
    if not r:
        return None
    try:
        key = get_unread_key(user_id)
        if not r.exists(key):
            cached_map = warmup_user_unread_cache(user_id)
            return sum(cached_map.values())
        all_vals = r.hgetall(key)
        return sum(int(v) for v in all_vals.values() if v.isdigit())
    except Exception as e:
        logger.warning(f"Redis get_user_total_unread error for {user_id}: {e}")
        return None

def increment_user_unread(user_id, room_id, amount=1):
    r = get_redis_client()
    if not r:
        return
    try:
        key = get_unread_key(user_id)
        if not r.exists(key):
            warmup_user_unread_cache(user_id)
        r.hincrby(key, str(room_id), amount)
        r.expire(key, 86400 * 7) # 7 days TTL
    except Exception as e:
        logger.warning(f"Redis increment_user_unread error for {user_id}, room {room_id}: {e}")

def reset_user_room_unread(user_id, room_id):
    r = get_redis_client()
    if not r:
        return
    try:
        key = get_unread_key(user_id)
        r.hset(key, str(room_id), 0)
        r.expire(key, 86400 * 7)
    except Exception as e:
        logger.warning(f"Redis reset_user_room_unread error for {user_id}, room {room_id}: {e}")

def warmup_user_unread_cache(user_id):
    from .models import ChatMessage, RoomParticipant
    r = get_redis_client()
    result = {}
    try:
        participants = RoomParticipant.objects.filter(user_id=user_id)
        for p in participants:
            count = ChatMessage.objects.filter(
                room=p.room,
                is_deleted=False
            ).exclude(
                sender_id=user_id
            ).exclude(
                recipient_statuses__user_id=user_id,
                recipient_statuses__status='READ'
            ).count()
            result[str(p.room_id)] = count

        if r:
            key = get_unread_key(user_id)
            if result:
                r.hset(key, mapping={k: str(v) for k, v in result.items()})
            else:
                r.hset(key, "_initialized", "1")
            r.expire(key, 86400 * 7)
    except Exception as e:
        logger.warning(f"Error warming up unread cache for {user_id}: {e}")
    return result
