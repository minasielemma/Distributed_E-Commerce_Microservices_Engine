import os
import logging
import requests

logger = logging.getLogger(__name__)

def log_audit_event(request, action, resource_type="", resource_id="", status="SUCCESS", details=None, changes=None):
    """
    Sends a non-blocking internal HTTP POST to identity_service to record a production audit log event.
    Safely redacts sensitive parameters.
    """
    try:
        identity_host = os.getenv("IDENTITY_SERVICE_HOST", "identity_service")
        target_url = f"http://{identity_host}:8000/api/auth/audit-logs/create-internal/"

        user = getattr(request, 'user', None)
        actor_id = getattr(user, 'id', None) if user and hasattr(user, 'id') else None
        actor_email = getattr(user, 'email', '') or getattr(user, 'username', '') if user else ''
        actor_role = getattr(user, 'role', '') if user else ''
        tenant_id = getattr(user, 'tenant_id', None) or request.headers.get('X-Tenant-Id')

        meta = getattr(request, 'META', {})
        ip_address = meta.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or meta.get('REMOTE_ADDR')
        user_agent = meta.get('HTTP_USER_AGENT', '')

        clean_details = dict(details) if isinstance(details, dict) else {}
        for secret_key in ['password', 'token', 'secret', 'credit_card', 'cvv']:
            if secret_key in clean_details:
                clean_details[secret_key] = '***REDACTED***'

        payload = {
            'tenant_id': str(tenant_id) if tenant_id and str(tenant_id) != 'None' else None,
            'actor_id': str(actor_id) if actor_id and str(actor_id) != 'None' else None,
            'actor_email': str(actor_email),
            'actor_role': str(actor_role),
            'action': action,
            'resource_type': resource_type,
            'resource_id': str(resource_id),
            'status': status,
            'ip_address': ip_address,
            'user_agent': user_agent[:255] if user_agent else '',
            'details': clean_details,
            'changes': changes or {}
        }

        requests.post(target_url, json=payload, timeout=2)
    except Exception as e:
        logger.warning(f"Failed to record audit log '{action}': {e}")
