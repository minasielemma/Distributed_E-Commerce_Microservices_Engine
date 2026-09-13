"""Checkout Redis distributed lock utility.

Used in CreateOrderView to prevent a single user from submitting concurrent
orders (double-click, tab racing, mobile retry).

Usage:
    with checkout_lock(customer_id):
        # safe to proceed with order creation
"""
import contextlib 
import logging 
import time 

logger =logging .getLogger (__name__ )

_LOCK_TTL =30 
_WAIT_INTERVAL =0.1 
_MAX_WAIT =5 


@contextlib .contextmanager 
def checkout_lock (customer_id ):
    """Acquire a per-customer checkout lock via Redis.

    Falls back gracefully if Redis is unavailable — the system is still
    correct (orders are protected by DB-level constraints), just not
    distributed-lock protected.
    """
    lock_key =f"checkout:lock:{customer_id }"
    redis_client =_get_redis ()

    if redis_client is None :
        logger .warning ("[CheckoutLock] Redis unavailable — proceeding without lock.")
        yield 
        return 

    lock =redis_client .lock (lock_key ,timeout =_LOCK_TTL ,blocking_timeout =_MAX_WAIT )
    acquired =False 
    try :
        acquired =lock .acquire (blocking =True )
        if not acquired :
            raise CheckoutLockError (
            "Another checkout is already in progress for this account. "
            "Please wait a moment and try again."
            )
        yield 
    finally :
        if acquired :
            try :
                lock .release ()
            except Exception :
                pass 


class CheckoutLockError (Exception ):
    """Raised when the checkout lock cannot be acquired."""


def _get_redis ():
    try :
        import redis 
        from django .conf import settings 
        redis_url =getattr (settings ,'REDIS_URL','redis://redis:6379/0')
        client =redis .Redis .from_url (redis_url )
        client .ping ()
        return client 
    except Exception as e :
        logger .debug (f"[CheckoutLock] Redis connect failed: {e }")
        return None 
