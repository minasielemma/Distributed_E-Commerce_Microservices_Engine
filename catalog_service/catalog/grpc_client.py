import os
import grpc
from catalog.inventory_pb2 import InitProductItemRequest
from catalog.inventory_pb2_grpc import InventoryServiceStub
from catalog.identity_pb2 import AuditLogRequest
from catalog.identity_pb2_grpc import IdentityServiceStub

INVENTORY_GRPC_HOST = os.getenv('INVENTORY_GRPC_HOST', 'inventory_service:50052')
IDENTITY_GRPC_HOST = os.getenv('IDENTITY_GRPC_HOST', 'identity_service:50053')
KEYS_DIR = os.getenv('KEYS_DIR', '/shared_keys')


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


def _get_channel(host):
    creds = _get_channel_credentials()
    if creds:
        options = [('grpc.ssl_target_name_override', 'catalog_service')]
        return grpc.secure_channel(host, creds, options=options)
    return grpc.insecure_channel(host)


def init_inventory_product(product_id_str, sku_str, quantity=100):
    try:
        channel = _get_channel(INVENTORY_GRPC_HOST)
        stub = InventoryServiceStub(channel)
        response = stub.InitProductItem(InitProductItemRequest(
            product_id=str(product_id_str),
            sku=str(sku_str or ''),
            quantity=int(quantity)
        ), timeout=5)
        return response
    except Exception as e:
        print(f"[Catalog Service] gRPC error calling Inventory InitProductItem: {e}")
        return None


def send_audit_log_grpc(service_name="catalog_service", action="", user_id="", tenant_id="", details=""):
    try:
        channel = _get_channel(IDENTITY_GRPC_HOST)
        stub = IdentityServiceStub(channel)
        response = stub.CreateAuditLog(AuditLogRequest(
            service_name=service_name,
            action=action,
            user_id=str(user_id or ''),
            tenant_id=str(tenant_id or ''),
            details=details
        ), timeout=5)
        return response
    except Exception as e:
        print(f"[Catalog Service] gRPC error calling Identity CreateAuditLog: {e}")
        return None
