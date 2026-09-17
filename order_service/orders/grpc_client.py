import os
import grpc
from orders.catalog_pb2 import (
    ProductRequest,
    CouponValidateRequest,
    CouponRedeemRequest,
    CouponReverseRequest
)
from orders.catalog_pb2_grpc import ProductServiceStub
from orders.inventory_pb2 import (
    StockCheckRequest,
    ReleaseStockRequest,
    CommitStockRequest
)
from orders.inventory_pb2_grpc import InventoryServiceStub
from orders.cart_pb2 import ClearCartRequest
from orders.cart_pb2_grpc import CartServiceStub
from orders.payment_pb2 import CheckoutRequest
from orders.payment_pb2_grpc import PaymentServiceStub
from orders.finance_pb2 import RecordPaymentRequest
from orders.finance_pb2_grpc import FinanceServiceStub
from orders.identity_pb2 import NotificationRequest
from orders.identity_pb2_grpc import IdentityServiceStub

CATALOG_GRPC_HOST = os.getenv('CATALOG_GRPC_HOST', 'catalog_service:50051')
INVENTORY_GRPC_HOST = os.getenv('INVENTORY_GRPC_HOST', 'inventory_service:50052')
IDENTITY_GRPC_HOST = os.getenv('IDENTITY_GRPC_HOST', 'identity_service:50053')
PAYMENT_GRPC_HOST = os.getenv('PAYMENT_GRPC_HOST', 'payment_service:50055')
FINANCE_GRPC_HOST = os.getenv('FINANCE_GRPC_HOST', 'finance_service:50056')
CART_GRPC_HOST = os.getenv('CART_GRPC_HOST', 'cart_service:50057')
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


def get_catalog_product(product_id_str):
    try:
        channel = _get_channel(CATALOG_GRPC_HOST)
        stub = ProductServiceStub(channel)
        response = stub.GetProduct(ProductRequest(id=str(product_id_str)), timeout=5)
        return response
    except grpc.RpcError as e:
        print(f"[Order Service] gRPC Error calling Catalog Service: {e.code()} - {e.details()}")
        raise Exception(f"Catalog Service unreachable via gRPC: {e.details()}")


def check_inventory_stock(product_id_str, requested_quantity=1):
    try:
        channel = _get_channel(INVENTORY_GRPC_HOST)
        stub = InventoryServiceStub(channel)
        response = stub.CheckStock(StockCheckRequest(
            product_id=str(product_id_str),
            requested_quantity=int(requested_quantity)
        ), timeout=5)
        return response
    except grpc.RpcError as e:
        print(f"[Order Service] gRPC Error calling Inventory Service: {e.code()} - {e.details()}")
        raise Exception(f"Inventory Service unreachable via gRPC: {e.details()}")


def validate_coupon_grpc(code_str, tenant_id_str="", subtotal_float=0.0):
    try:
        channel = _get_channel(CATALOG_GRPC_HOST)
        stub = ProductServiceStub(channel)
        response = stub.ValidateCoupon(CouponValidateRequest(
            code=code_str,
            tenant_id=str(tenant_id_str or ""),
            order_total=float(subtotal_float)
        ), timeout=5)
        return response
    except Exception as e:
        print(f"[Order Service] gRPC error calling ValidateCoupon: {e}")
        return None


def redeem_coupon_grpc(code_str, tenant_id_str="", order_id_str="", subtotal_float=0.0):
    try:
        channel = _get_channel(CATALOG_GRPC_HOST)
        stub = ProductServiceStub(channel)
        response = stub.RedeemCoupon(CouponRedeemRequest(
            code=code_str,
            tenant_id=str(tenant_id_str or ""),
            order_id=str(order_id_str),
            order_total=float(subtotal_float)
        ), timeout=5)
        return response
    except Exception as e:
        print(f"[Order Service] gRPC error calling RedeemCoupon: {e}")
        return None


def reverse_coupon_grpc(order_id_str):
    try:
        channel = _get_channel(CATALOG_GRPC_HOST)
        stub = ProductServiceStub(channel)
        response = stub.ReverseCoupon(CouponReverseRequest(order_id=str(order_id_str)), timeout=5)
        return response
    except Exception as e:
        print(f"[Order Service] gRPC error calling ReverseCoupon: {e}")
        return None


def clear_cart_grpc(user_id_str):
    try:
        channel = _get_channel(CART_GRPC_HOST)
        stub = CartServiceStub(channel)
        response = stub.ClearCart(ClearCartRequest(user_id=str(user_id_str)), timeout=5)
        return response
    except Exception as e:
        print(f"[Order Service] gRPC error calling ClearCart: {e}")
        return None


def release_stock_grpc(order_id_str):
    try:
        channel = _get_channel(INVENTORY_GRPC_HOST)
        stub = InventoryServiceStub(channel)
        response = stub.ReleaseStock(ReleaseStockRequest(order_id=str(order_id_str)), timeout=5)
        return response
    except Exception as e:
        print(f"[Order Service] gRPC error calling ReleaseStock: {e}")
        return None


def commit_stock_grpc(order_id_str):
    try:
        channel = _get_channel(INVENTORY_GRPC_HOST)
        stub = InventoryServiceStub(channel)
        response = stub.CommitStock(CommitStockRequest(order_id=str(order_id_str)), timeout=5)
        return response
    except Exception as e:
        print(f"[Order Service] gRPC error calling CommitStock: {e}")
        return None


def create_payment_checkout_grpc(order_id_str, amount_float=0.0, currency="USD", tenant_id_str="", user_id_str=""):
    try:
        channel = _get_channel(PAYMENT_GRPC_HOST)
        stub = PaymentServiceStub(channel)
        response = stub.CreateCheckout(CheckoutRequest(
            order_id=str(order_id_str),
            amount=float(amount_float),
            currency=currency,
            tenant_id=str(tenant_id_str or ""),
            user_id=str(user_id_str or "")
        ), timeout=20)
        return response
    except Exception as e:
        print(f"[Order Service] gRPC error calling CreateCheckout: {e}")
        raise Exception(f"Connection refused by payment service: {e}")


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
        print(f"[Order Service] gRPC error calling RecordLedgerPayment: {e}")
        return None


def send_notification_grpc(recipient_id="", tenant_id="", title="", message="", notification_type="SYSTEM"):
    try:
        channel = _get_channel(IDENTITY_GRPC_HOST)
        stub = IdentityServiceStub(channel)
        response = stub.CreateInternalNotification(NotificationRequest(
            recipient_id=str(recipient_id or ""),
            tenant_id=str(tenant_id or ""),
            title=title,
            message=message,
            notification_type=notification_type
        ), timeout=5)
        return response
    except Exception as e:
        print(f"[Order Service] gRPC error calling CreateInternalNotification: {e}")
        return None
