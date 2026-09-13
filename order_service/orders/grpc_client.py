import os
import grpc
from .catalog_pb2 import ProductRequest
from .catalog_pb2_grpc import ProductServiceStub
from .inventory_pb2 import StockCheckRequest
from .inventory_pb2_grpc import InventoryServiceStub

CATALOG_GRPC_HOST = os.getenv('CATALOG_GRPC_HOST', 'catalog_service:50051')
INVENTORY_GRPC_HOST = os.getenv('INVENTORY_GRPC_HOST', 'inventory_service:50052')
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


def get_catalog_product(product_id_str):
    print(f"[Order Service] Connecting gRPC to {CATALOG_GRPC_HOST} for product {product_id_str}...")
    try:
        creds = _get_channel_credentials()
        if creds:
            channel = grpc.secure_channel(CATALOG_GRPC_HOST, creds)
        else:
            channel = grpc.insecure_channel(CATALOG_GRPC_HOST)
        stub = ProductServiceStub(channel)
        request = ProductRequest(id=str(product_id_str))
        response = stub.GetProduct(request, timeout=5)
        return response
    except grpc.RpcError as e:
        print(f"[Order Service] gRPC Error calling Catalog Service: {e.code()} - {e.details()}")
        raise Exception(f"Catalog Service unreachable via gRPC: {e.details()}")


def check_inventory_stock(product_id_str, requested_quantity=1):
    print(f"[Order Service] Connecting gRPC to {INVENTORY_GRPC_HOST} for inventory stock check...")
    try:
        creds = _get_channel_credentials()
        if creds:
            channel = grpc.secure_channel(INVENTORY_GRPC_HOST, creds)
        else:
            channel = grpc.insecure_channel(INVENTORY_GRPC_HOST)
        stub = InventoryServiceStub(channel)
        request = StockCheckRequest(
            product_id=str(product_id_str),
            requested_quantity=int(requested_quantity)
        )
        response = stub.CheckStock(request, timeout=5)
        return response
    except grpc.RpcError as e:
        print(f"[Order Service] gRPC Error calling Inventory Service: {e.code()} - {e.details()}")
        raise Exception(f"Inventory Service unreachable via gRPC: {e.details()}")
