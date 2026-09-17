import os
import sys
import uuid
import concurrent.futures
import grpc
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "payment_project.settings")
django.setup()

from decimal import Decimal
from payments.models import Payment
from payments.polar_provider import PolarPaymentProvider, get_polar_checkout_base_url
from payments.payment_pb2 import (
    CheckoutResponse
)
from payments.payment_pb2_grpc import PaymentServiceServicer, add_PaymentServiceServicer_to_server

KEYS_DIR = os.getenv("KEYS_DIR", "/shared_keys")


class PaymentServicer(PaymentServiceServicer):
    def CreateCheckout(self, request, context):
        order_id_str = request.order_id
        amount = Decimal(str(request.amount or 0.0))

        try:
            oid = uuid.UUID(order_id_str)
            cust_id = uuid.UUID(request.user_id) if request.user_id else uuid.uuid4()
            ten_id = uuid.UUID(request.tenant_id) if request.tenant_id else None

            payment, created = Payment.objects.get_or_create(
                order_id=oid,
                defaults={
                    'tenant_id': ten_id,
                    'customer_id': cust_id,
                    'amount': amount,
                    'provider': 'POLAR',
                    'status': 'PENDING',
                }
            )

            if not payment.polar_checkout_url:
                try:
                    provider = PolarPaymentProvider()
                    session_info = provider.create_checkout_session(
                        order_id=oid,
                        customer_id=cust_id,
                        amount=amount
                    )
                    if 'error' not in session_info and session_info.get('checkout_url'):
                        payment.polar_checkout_id = session_info.get('checkout_id')
                        payment.polar_checkout_url = session_info.get('checkout_url')
                        payment.save()
                except Exception as polar_err:
                    import logging
                    logging.getLogger(__name__).warning(f"Could not create Polar checkout session in gRPC: {polar_err}")

            checkout_base = get_polar_checkout_base_url()
            checkout_url = payment.polar_checkout_url or f"{checkout_base}/polar_chk_{payment.id}"
            return CheckoutResponse(
                success=True,
                checkout_url=checkout_url,
                payment_id=str(payment.id),
                status=payment.status,
                error_message=""
            )

        except Exception as e:
            return CheckoutResponse(
                success=False,
                checkout_url="",
                payment_id="",
                status="FAILED",
                error_message=str(e)
            )


def serve():
    port = os.getenv("GRPC_PORT", "50055")
    server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=10))
    add_PaymentServiceServicer_to_server(PaymentServicer(), server)

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
        print(f"[Payment gRPC Server] Running on port {port} with mTLS...")
    else:
        server.add_insecure_port(f"[::]:{port}")
        print(f"[Payment gRPC Server] Running on port {port} (insecure fallback)...")

    server.start()
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == "__main__":
    serve()
