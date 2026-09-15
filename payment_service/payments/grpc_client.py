import os
import grpc
from payments.catalog_pb2 import (
    ProductRequest,
    PolarIdRequest,
    CouponConfirmRequest
)
from payments.catalog_pb2_grpc import ProductServiceStub
from payments.order_pb2 import MarkPaidRequest
from payments.order_pb2_grpc import OrderServiceStub
from payments.finance_pb2 import RecordPaymentRequest
from payments.finance_pb2_grpc import FinanceServiceStub

CATALOG_GRPC_HOST = os.getenv('CATALOG_GRPC_HOST', 'catalog_service:50051')
ORDER_GRPC_HOST = os.getenv('ORDER_GRPC_HOST', 'order_service:50054')
FINANCE_GRPC_HOST = os.getenv('FINANCE_GRPC_HOST', 'finance_service:50056')
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
        print(f"[Payment Service] gRPC error calling Catalog GetProduct: {e}")
        return None


def get_product_polar_id_grpc(product_id_str):
    try:
        channel = _get_channel(CATALOG_GRPC_HOST)
        stub = ProductServiceStub(channel)
        response = stub.GetProductPolarId(PolarIdRequest(product_id=str(product_id_str)), timeout=5)
        return response
    except Exception as e:
        print(f"[Payment Service] gRPC error calling Catalog GetProductPolarId: {e}")
        return None


def confirm_coupon_grpc(order_id_str):
    try:
        channel = _get_channel(CATALOG_GRPC_HOST)
        stub = ProductServiceStub(channel)
        response = stub.ConfirmCoupon(CouponConfirmRequest(order_id=str(order_id_str)), timeout=5)
        return response
    except Exception as e:
        print(f"[Payment Service] gRPC error calling Catalog ConfirmCoupon: {e}")
        return None


def mark_order_paid_grpc(order_id_str):
    try:
        channel = _get_channel(ORDER_GRPC_HOST)
        stub = OrderServiceStub(channel)
        response = stub.MarkOrderPaid(MarkPaidRequest(order_id=str(order_id_str)), timeout=5)
        return response
    except Exception as e:
        print(f"[Payment Service] gRPC error calling Order MarkOrderPaid: {e}")
        return None


def record_ledger_payment_grpc(tenant_id_str, order_id_str, payment_id_str="", amount_float=0.0, currency="USD", payment_method="CARD"):
    try:
        channel = _get_channel(FINANCE_GRPC_HOST)
        stub = FinanceServiceStub(channel)
        response = stub.RecordLedgerPayment(RecordPaymentRequest(
            tenant_id=str(tenant_id_str or ""),
            order_id=str(order_id_str),
            payment_id=str(payment_id_str or ""),
            amount=float(amount_float),
            currency=currency,
            payment_method=payment_method
        ), timeout=5)
        return response
    except Exception as e:
        print(f"[Payment Service] gRPC error calling Finance RecordLedgerPayment: {e}")
        return None
