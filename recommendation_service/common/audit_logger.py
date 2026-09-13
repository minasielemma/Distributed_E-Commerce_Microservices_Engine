import logging

logger = logging.getLogger('audit')

def log_audit_event(action, user_id=None, details=None, tenant_id=None):
    logger.info(f"AUDIT: action={action} user_id={user_id} tenant_id={tenant_id} details={details}")
