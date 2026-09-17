import os
import sys
import concurrent.futures
import grpc
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "finance_project.settings")
django.setup()

from decimal import Decimal
from finance.accounting_utils import record_payment_ledger_and_invoice
from finance.finance_pb2 import (
    RecordPaymentResponse
)
from finance.finance_pb2_grpc import FinanceServiceServicer, add_FinanceServiceServicer_to_server

KEYS_DIR = os.getenv("KEYS_DIR", "/shared_keys")


class FinanceServicer(FinanceServiceServicer):
    def RecordLedgerPayment(self, request, context):
        tenant_id = request.tenant_id
        order_id = request.order_id
        payment_id = request.payment_id
        amount = Decimal(str(request.amount or 0.0))
        payment_method = request.payment_method or 'CARD'

        try:
            entry, invoice, ledger_entry = record_payment_ledger_and_invoice(
                order_id=order_id,
                customer_id=payment_id or "customer_anon",
                tenant_id=tenant_id,
                total_amount=amount
            )
            entry_id = str(entry.id) if entry and hasattr(entry, 'id') else (str(invoice.id) if invoice else "")
            return RecordPaymentResponse(
                success=True,
                entry_id=entry_id,
                error_message=""
            )
        except Exception as e:
            print(f"[Finance gRPC] Error in RecordLedgerPayment: {str(e)}")
            return RecordPaymentResponse(
                success=False,
                entry_id="",
                error_message=str(e)
            )


def serve():
    port = os.getenv("GRPC_PORT", "50056")
    server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=10))
    add_FinanceServiceServicer_to_server(FinanceServicer(), server)

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
        print(f"[Finance gRPC Server] Running on port {port} with mTLS...")
    else:
        server.add_insecure_port(f"[::]:{port}")
        print(f"[Finance gRPC Server] Running on port {port} (insecure fallback)...")

    server.start()
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == "__main__":
    serve()
