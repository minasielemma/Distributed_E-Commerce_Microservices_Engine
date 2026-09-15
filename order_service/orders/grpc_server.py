import os
import sys
import uuid
import concurrent.futures
import grpc
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "order_project.settings")
django.setup()

from orders.models import Order
from orders.order_pb2 import (
    GetOrderResponse,
    MarkPaidResponse
)
from orders.order_pb2_grpc import OrderServiceServicer, add_OrderServiceServicer_to_server

KEYS_DIR = os.getenv("KEYS_DIR", "/shared_keys")


class OrderServicer(OrderServiceServicer):
    def GetOrder(self, request, context):
        order_id_str = request.order_id
        try:
            oid = uuid.UUID(order_id_str)
            order = Order.objects.get(id=oid)
            return GetOrderResponse(
                order_id=str(order.id),
                customer_id=str(order.customer_id or ''),
                tenant_id=str(order.tenant_id or ''),
                status=order.status,
                total_amount=float(order.total_amount),
                created_at=str(order.created_at),
                found=True,
                error_message=""
            )
        except Order.DoesNotExist:
            return GetOrderResponse(
                order_id=order_id_str, customer_id="", tenant_id="", status="",
                total_amount=0.0, created_at="", found=False, error_message="Order not found"
            )
        except Exception as e:
            return GetOrderResponse(
                order_id=order_id_str, customer_id="", tenant_id="", status="",
                total_amount=0.0, created_at="", found=False, error_message=str(e)
            )

    def MarkOrderPaid(self, request, context):
        order_id_str = request.order_id
        try:
            oid = uuid.UUID(order_id_str)
            order = Order.objects.get(id=oid)
            if order.status != 'PAID':
                order.status = 'PAID'
                order.save(update_fields=['status'])
            return MarkPaidResponse(success=True, status=order.status, message="Order marked as paid")
        except Order.DoesNotExist:
            return MarkPaidResponse(success=False, status="", message="Order not found")
        except Exception as e:
            return MarkPaidResponse(success=False, status="", message=str(e))


def serve():
    port = os.getenv("GRPC_PORT", "50054")
    server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=10))
    add_OrderServiceServicer_to_server(OrderServicer(), server)

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
        print(f"[Order gRPC Server] Running on port {port} with mTLS...")
    else:
        server.add_insecure_port(f"[::]:{port}")
        print(f"[Order gRPC Server] Running on port {port} (insecure fallback)...")

    server.start()
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == "__main__":
    serve()
