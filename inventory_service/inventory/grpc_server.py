import os
import sys
import concurrent.futures
import grpc
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "inventory_project.settings")
django.setup()

from django.db import models, transaction
from inventory.models.inventory_item import InventoryItem
from inventory.inventory_pb2 import (
    StockCheckResponse,
    ReleaseStockResponse,
    CommitStockResponse,
    InitProductItemResponse
)
from inventory.inventory_pb2_grpc import InventoryServiceServicer, add_InventoryServiceServicer_to_server

KEYS_DIR = os.getenv("KEYS_DIR", "/shared_keys")


class InventoryServicer(InventoryServiceServicer):
    def CheckStock(self, request, context):
        product_id_str = request.product_id
        requested_qty = request.requested_quantity

        try:
            items = InventoryItem.objects.filter(product_id=product_id_str)
            total_avail = items.aggregate(total=models.Sum('quantity_available'))['total'] or 0
            is_avail = total_avail >= requested_qty

            return StockCheckResponse(
                product_id=product_id_str,
                is_available=is_avail,
                current_stock=total_avail,
                error_message="" if is_avail else f"Insufficient stock: requested {requested_qty}, available {total_avail}"
            )
        except Exception as e:
            return StockCheckResponse(
                product_id=product_id_str,
                is_available=False,
                current_stock=0,
                error_message=f"Stock check error: {str(e)}"
            )

    def ReleaseStock(self, request, context):
        try:
            # Release stock logic
            return ReleaseStockResponse(success=True, message=f"Stock released for order {request.order_id}")
        except Exception as e:
            return ReleaseStockResponse(success=False, message=str(e))

    def CommitStock(self, request, context):
        try:
            # Commit stock logic
            return CommitStockResponse(success=True, message=f"Stock committed for order {request.order_id}")
        except Exception as e:
            return CommitStockResponse(success=False, message=str(e))

    def InitProductItem(self, request, context):
        try:
            with transaction.atomic():
                item, created = InventoryItem.objects.get_or_create(
                    product_id=request.product_id,
                    defaults={
                        'sku': request.sku or f"SKU-{request.product_id[:8]}",
                        'quantity_available': request.quantity or 100,
                        'quantity_reserved': 0
                    }
                )
                if not created and request.quantity:
                    item.quantity_available = request.quantity
                    item.save(update_fields=['quantity_available'])
            return InitProductItemResponse(success=True, message="Inventory item initialized")
        except Exception as e:
            return InitProductItemResponse(success=False, message=str(e))


def serve():
    port = os.getenv("GRPC_PORT", "50052")
    server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=10))
    add_InventoryServiceServicer_to_server(InventoryServicer(), server)

    server_cert_path = os.path.join(KEYS_DIR, "grpc_server.crt")
    server_key_path = os.path.join(KEYS_DIR, "grpc_server.key")
    ca_cert_path = os.path.join(KEYS_DIR, "grpc_ca.crt")

    if os.path.exists(server_cert_path) and os.path.exists(server_key_path) and os.path.exists(ca_cert_path):
        server_cert = open(server_cert_path, "rb").read()
        server_key = open(server_key_path, "rb").read()
        ca_cert = open(ca_cert_path, "rb").read()
        credentials = grpc.ssl_server_credentials(
            [(server_key, server_cert)],
            root_certificates=ca_cert,
            require_client_auth=True,
        )
        server.add_secure_port(f"[::]:{port}", credentials)
        print(f"[Inventory gRPC Server] Running on port {port} with mTLS...")
    else:
        server.add_insecure_port(f"[::]:{port}")
        print(f"[Inventory gRPC Server] Running on port {port} (insecure fallback)...")

    server.start()
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == "__main__":
    serve()
