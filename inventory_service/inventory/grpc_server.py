import os
import sys
import time
import concurrent.futures
import grpc
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "inventory_project.settings")
django.setup()

from django.db import models
from inventory.models.inventory_item import InventoryItem
from inventory.inventory_pb2 import StockCheckResponse
from inventory.inventory_pb2_grpc import InventoryServiceServicer, add_InventoryServiceServicer_to_server


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


def serve():
    port = os.getenv("GRPC_PORT", "50052")
    server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=10))
    add_InventoryServiceServicer_to_server(InventoryServicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f"[Inventory gRPC Server] Running on port {port}...")
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == "__main__":
    serve()
