import os
import concurrent.futures
import grpc
from django.core.management.base import BaseCommand
from catalog.models import Product
from catalog.catalog_pb2 import ProductResponse
from catalog.catalog_pb2_grpc import ProductServiceServicer, add_ProductServiceServicer_to_server

KEYS_DIR = os.getenv("KEYS_DIR", "/shared_keys")

class ProductService(ProductServiceServicer):
    """
    gRPC Server for Catalog Service.
    Order Service queries `GetProduct` to verify product details and unit price.
    """
    def GetProduct(self, request, context):
        product_id = request.id
        print(f"[Catalog gRPC] Received GetProduct request for ID: {product_id}")

        try:
            product = Product.objects.get(id=product_id)
            stock_count = sum(v.stock for v in product.variants.all()) if product.variants.exists() else 100
            return ProductResponse(
                id=str(product.id),
                title=product.name,
                price=float(product.dynamic_price),
                stock_count=stock_count,
                found=True,
                error_message=""
            )
        except Product.DoesNotExist:
            print(f"[Catalog gRPC] Product {product_id} not found.")
            return ProductResponse(
                id=product_id,
                title="",
                price=0.0,
                stock_count=0,
                found=False,
                error_message=f"Product with ID {product_id} not found"
            )
        except Exception as e:
            print(f"[Catalog gRPC] Error fetching product: {str(e)}")
            return ProductResponse(
                id=product_id,
                title="",
                price=0.0,
                stock_count=0,
                found=False,
                error_message=str(e)
            )

class Command(BaseCommand):
    help = 'Starts the Catalog Service gRPC server on port 50051'

    def handle(self, *args, **options):
        server_cert = open(os.path.join(KEYS_DIR, "grpc_server.crt"), "rb").read()
        server_key = open(os.path.join(KEYS_DIR, "grpc_server.key"), "rb").read()
        ca_cert = open(os.path.join(KEYS_DIR, "grpc_ca.crt"), "rb").read()

        credentials = grpc.ssl_server_credentials(
            [(server_key, server_cert)],
            root_certificates=ca_cert,
            require_client_auth=True,
        )

        server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=10))
        add_ProductServiceServicer_to_server(ProductService(), server)
        server.add_secure_port('[::]:50051', credentials)
        print("[Catalog Service] gRPC Server running on port 50051 with mTLS...")
        server.start()
        server.wait_for_termination()
