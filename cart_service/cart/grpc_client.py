import os
import grpc
from cart.catalog_pb2 import ProductRequest, CouponValidateRequest
from cart.catalog_pb2_grpc import ProductServiceStub
from cart.identity_pb2 import NotificationRequest
from cart.identity_pb2_grpc import IdentityServiceStub

CATALOG_GRPC_HOST = os.getenv('CATALOG_GRPC_HOST', 'catalog_service:50051')
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


def get_catalog_product(product_id_str):
    try:
        channel = _get_channel(CATALOG_GRPC_HOST)
        stub = ProductServiceStub(channel)
        response = stub.GetProduct(ProductRequest(id=str(product_id_str)), timeout=5)
        return response
    except Exception as e:
        print(f"[Cart Service] gRPC error calling Catalog GetProduct: {e}")
        return None


def validate_coupon_grpc(code_str, subtotal_float=0.0):
    try:
        channel = _get_channel(CATALOG_GRPC_HOST)
        stub = ProductServiceStub(channel)
        response = stub.ValidateCoupon(CouponValidateRequest(code=code_str, order_total=subtotal_float), timeout=5)
        return response
    except Exception as e:
        print(f"[Cart Service] gRPC error calling Catalog ValidateCoupon: {e}")
        return None


def send_notification_grpc(recipient_id="", tenant_id="", title="", message="", notification_type="ITEM_REQUEST"):
    try:
        channel = _get_channel(IDENTITY_GRPC_HOST)
        stub = IdentityServiceStub(channel)
        response = stub.CreateInternalNotification(NotificationRequest(
            recipient_id=str(recipient_id or ""),
            tenant_id=str(tenant_id or ""),
            title=title,
            message=message,
            notification_type=notification_type
        ), timeout=5)
        return response
    except Exception as e:
        print(f"[Cart Service] gRPC error calling Identity CreateInternalNotification: {e}")
        return None
