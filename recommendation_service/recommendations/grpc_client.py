import os
import grpc
from recommendations.catalog_pb2 import ProductRequest, ListProductsRequest
from recommendations.catalog_pb2_grpc import ProductServiceStub

CATALOG_GRPC_HOST = os.getenv('CATALOG_GRPC_HOST', 'catalog_service:50051')
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
        target_name = host.split(':')[0].replace('-', '_')
        options = [('grpc.ssl_target_name_override', target_name)]
        return grpc.secure_channel(host, creds, options=options)
    return grpc.insecure_channel(host)


def get_catalog_product_grpc(product_id_str):
    try:
        channel = _get_channel(CATALOG_GRPC_HOST)
        stub = ProductServiceStub(channel)
        response = stub.GetProduct(ProductRequest(id=str(product_id_str)), timeout=5)
        return response
    except Exception as e:
        print(f"[Recommendation Service] gRPC error in GetProduct: {e}")
        return None


def list_catalog_products_grpc(page=1, page_size=100):
    try:
        channel = _get_channel(CATALOG_GRPC_HOST)
        stub = ProductServiceStub(channel)
        response = stub.ListProducts(ListProductsRequest(page=page, page_size=page_size), timeout=5)
        return response.products
    except Exception as e:
        print(f"[Recommendation Service] gRPC error in ListProducts: {e}")
        return []
