import os
import json
import logging
import grpc
from orders.identity_pb2 import AuditLogRequest
from orders.identity_pb2_grpc import IdentityServiceStub

logger = logging.getLogger(__name__)

KEYS_DIR = os.getenv('KEYS_DIR', '/shared_keys')
IDENTITY_GRPC_HOST = os.getenv('IDENTITY_GRPC_HOST', 'identity_service:50053')


def _get_channel_credentials():
    ca_path = os.path.join(KEYS_DIR, 'grpc_ca.crt')
    client_cert_path = os.path.join(KEYS_DIR, 'grpc_client.crt')
    client_key_path = os.path.join(KEYS_DIR, 'grpc_client.key')

    if os.path.exists(ca_path) and os.path.exists(client_cert_path) and os.path.exists(client_key_path):
        ca_cert = open(ca_path, 'rb').read()
        client_cert = open(client_cert_path, 'rb').read()
        client_key = open(client_key_path, 'rb').read()
        return grpc.ssl_channel_credentials(
            root_certificates=ca_cert,
            private_key=client_key,
            certificate_chain=client_cert,
        )
    return None


def log_audit_event(request, action, resource_type="", resource_id="", status="SUCCESS", details=None, changes=None):
    try:
        user = getattr(request, 'user', None)
        actor_id = getattr(user, 'id', None) if user and hasattr(user, 'id') else None
        tenant_id = getattr(user, 'tenant_id', None) or (request.headers.get('X-Tenant-Id') if hasattr(request, 'headers') else None)

        clean_details = dict(details) if isinstance(details, dict) else {}
        for secret_key in ['password', 'token', 'secret', 'credit_card', 'cvv']:
            if secret_key in clean_details:
                clean_details[secret_key] = '***REDACTED***'

        creds = _get_channel_credentials()
        options = [('grpc.ssl_target_name_override', 'catalog_service')] if creds else None
        channel = grpc.secure_channel(IDENTITY_GRPC_HOST, creds, options=options) if creds else grpc.insecure_channel(IDENTITY_GRPC_HOST)
        stub = IdentityServiceStub(channel)
        stub.CreateAuditLog(AuditLogRequest(
            service_name="order_service",
            action=action,
            user_id=str(actor_id or ''),
            tenant_id=str(tenant_id or ''),
            details=json.dumps(clean_details)
        ), timeout=2)
    except Exception as e:
        logger.warning(f"Failed to record audit log '{action}' via gRPC: {e}")
