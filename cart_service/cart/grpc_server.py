import os
import sys
import concurrent.futures
import grpc
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cart_project.settings")
django.setup()

from cart.models import Cart
from cart.cart_pb2 import (
    ClearCartResponse
)
from cart.cart_pb2_grpc import CartServiceServicer, add_CartServiceServicer_to_server

KEYS_DIR = os.getenv("KEYS_DIR", "/shared_keys")


class CartServicer(CartServiceServicer):
    def ClearCart(self, request, context):
        user_id_str = request.user_id
        session_id_str = request.session_id

        try:
            qs = Cart.objects.all()
            if user_id_str:
                qs = qs.filter(user_id=user_id_str)
            elif session_id_str:
                qs = qs.filter(session_id=session_id_str)
            else:
                return ClearCartResponse(success=False, message="User ID or Session ID required")

            for cart in qs:
                cart.items.all().delete()
            return ClearCartResponse(success=True, message="Cart cleared")
        except Exception as e:
            return ClearCartResponse(success=False, message=str(e))


def serve():
    port = os.getenv("GRPC_PORT", "50057")
    server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=10))
    add_CartServiceServicer_to_server(CartServicer(), server)

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
        print(f"[Cart gRPC Server] Running on port {port} with mTLS...")
    else:
        server.add_insecure_port(f"[::]:{port}")
        print(f"[Cart gRPC Server] Running on port {port} (insecure fallback)...")

    server.start()
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == "__main__":
    serve()
