import json
import logging
from datetime import datetime, timezone
from django.core.cache import cache
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)

PRESENCE_TTL = 300  # 5 minutes presence heartbeat timeout


def get_presence_key(user_id):
    return f"chat_presence:{user_id}"


def set_user_online(user_id, status='online'):
    if not user_id:
        return
    key = get_presence_key(user_id)
    data = {
        'status': status,
        'last_seen': datetime.now(timezone.utc).isoformat()
    }
    try:
        cache.set(key, data, timeout=PRESENCE_TTL)
    except Exception as e:
        logger.warning(f"Failed to set user presence in cache for {user_id}: {e}")


def set_user_offline(user_id):
    if not user_id:
        return
    key = get_presence_key(user_id)
    data = {
        'status': 'offline',
        'last_seen': datetime.now(timezone.utc).isoformat()
    }
    try:
        cache.set(key, data, timeout=PRESENCE_TTL)
    except Exception as e:
        logger.warning(f"Failed to set offline presence in cache for {user_id}: {e}")


def get_user_presence(user_id):
    if not user_id:
        return {'status': 'offline', 'last_seen': None}
    key = get_presence_key(user_id)
    try:
        val = cache.get(key)
        if val:
            return val
    except Exception as e:
        logger.warning(f"Failed to get user presence for {user_id}: {e}")
    return {'status': 'offline', 'last_seen': None}


def broadcast_presence_event(user_id, status='online'):
    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f"user_updates_{user_id}",
                {
                    'type': 'presence_update',
                    'data': {
                        'user_id': str(user_id),
                        'status': status,
                        'last_seen': datetime.now(timezone.utc).isoformat()
                    }
                }
            )
    except Exception as e:
        logger.warning(f"Failed to broadcast presence event: {e}")
