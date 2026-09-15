import os
import uuid
import concurrent.futures
from decimal import Decimal
import grpc
from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Product, DiscountCode, CouponRedemption
from catalog.catalog_pb2 import (
    ProductResponse,
    CouponValidateResponse,
    CouponRedeemResponse,
    CouponConfirmResponse,
    CouponReverseResponse,
    PolarIdResponse,
    ListProductsResponse
)
from catalog.catalog_pb2_grpc import ProductServiceServicer, add_ProductServiceServicer_to_server

KEYS_DIR = os.getenv("KEYS_DIR", "/shared_keys")


class ProductService(ProductServiceServicer):
    """
    gRPC Server for Catalog Service.
    Handles product lookups, coupon verification & redemption.
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
                tenant_id=str(product.tenant_id or ''),
                polar_id=str(getattr(product, 'polar_id', '') or ''),
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
                tenant_id="",
                polar_id="",
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
                tenant_id="",
                polar_id="",
                found=False,
                error_message=str(e)
            )

    def ValidateCoupon(self, request, context):
        code_str = request.code.strip().upper()
        subtotal = Decimal(str(request.order_total or 0.0))
        if not code_str:
            return CouponValidateResponse(is_valid=False, discount_amount=0.0, code="", error_message="Coupon code required")

        try:
            coupon = DiscountCode.objects.get(code__iexact=code_str)
            is_valid, msg = coupon.is_valid(subtotal=subtotal)
            if not is_valid:
                return CouponValidateResponse(is_valid=False, discount_amount=0.0, code=code_str, error_message=msg)
            discount_amount = coupon.calculate_discount(subtotal)
            return CouponValidateResponse(is_valid=True, discount_amount=float(discount_amount), code=coupon.code, error_message="")
        except DiscountCode.DoesNotExist:
            return CouponValidateResponse(is_valid=False, discount_amount=0.0, code=code_str, error_message="Invalid coupon code")
        except Exception as e:
            return CouponValidateResponse(is_valid=False, discount_amount=0.0, code=code_str, error_message=str(e))

    def RedeemCoupon(self, request, context):
        code_str = request.code.strip().upper()
        order_id_str = request.order_id.strip()
        subtotal = Decimal(str(request.order_total or 0.0))

        try:
            order_id = uuid.UUID(order_id_str)
        except Exception:
            return CouponRedeemResponse(success=False, discount_amount=0.0, error_message="Valid order_id UUID required")

        existing = CouponRedemption.objects.filter(
            order_id=order_id, status=CouponRedemption.STATUS_PENDING
        ).select_related('discount_code').first()
        if existing and existing.discount_code.code.upper() == code_str:
            return CouponRedeemResponse(success=True, discount_amount=float(existing.discount_amount), error_message="")

        with transaction.atomic():
            try:
                coupon = DiscountCode.objects.select_for_update().get(code__iexact=code_str)
                is_valid, msg = coupon.is_valid(subtotal=subtotal)
                if not is_valid:
                    return CouponRedeemResponse(success=False, discount_amount=0.0, error_message=msg)

                discount_amount = coupon.calculate_discount(subtotal)
                coupon.times_used += 1
                coupon.save(update_fields=['times_used'])

                CouponRedemption.objects.create(
                    discount_code=coupon,
                    order_id=order_id,
                    discount_amount=discount_amount,
                    status=CouponRedemption.STATUS_PENDING,
                )
                return CouponRedeemResponse(success=True, discount_amount=float(discount_amount), error_message="")
            except DiscountCode.DoesNotExist:
                return CouponRedeemResponse(success=False, discount_amount=0.0, error_message="Coupon code not found")
            except Exception as e:
                return CouponRedeemResponse(success=False, discount_amount=0.0, error_message=str(e))

    def ConfirmCoupon(self, request, context):
        try:
            oid = uuid.UUID(str(request.order_id))
            with transaction.atomic():
                redemption = CouponRedemption.objects.select_for_update().get(order_id=oid)
                if redemption.status != CouponRedemption.STATUS_REVERSED:
                    redemption.status = CouponRedemption.STATUS_CONFIRMED
                    redemption.save(update_fields=['status', 'updated_at'])
            return CouponConfirmResponse(success=True, message="confirmed")
        except Exception as e:
            return CouponConfirmResponse(success=False, message=str(e))

    def ReverseCoupon(self, request, context):
        try:
            oid = uuid.UUID(str(request.order_id))
            with transaction.atomic():
                redemption = CouponRedemption.objects.select_for_update().filter(order_id=oid).first()
                if redemption and redemption.status != CouponRedemption.STATUS_REVERSED:
                    redemption.status = CouponRedemption.STATUS_REVERSED
                    redemption.save(update_fields=['status', 'updated_at'])
                    coupon = redemption.discount_code
                    if coupon.times_used > 0:
                        coupon.times_used -= 1
                        coupon.save(update_fields=['times_used'])
            return CouponReverseResponse(success=True, status="reversed")
        except Exception as e:
            return CouponReverseResponse(success=False, status=str(e))

    def GetProductPolarId(self, request, context):
        try:
            product = Product.objects.get(id=request.product_id)
            return PolarIdResponse(product_id=str(product.id), polar_id=str(getattr(product, 'polar_id', '') or ''), found=True)
        except Exception:
            return PolarIdResponse(product_id=request.product_id, polar_id="", found=False)

    def ListProducts(self, request, context):
        try:
            products_qs = Product.objects.all()[:100]
            items = []
            for product in products_qs:
                stock_count = sum(v.stock for v in product.variants.all()) if product.variants.exists() else 100
                items.append(ProductResponse(
                    id=str(product.id),
                    title=product.name,
                    price=float(product.dynamic_price),
                    stock_count=stock_count,
                    tenant_id=str(product.tenant_id or ''),
                    polar_id=str(getattr(product, 'polar_id', '') or ''),
                    found=True,
                    error_message=""
                ))
            return ListProductsResponse(products=items, total_count=len(items))
        except Exception as e:
            return ListProductsResponse(products=[], total_count=0)


class Command(BaseCommand):
    help = 'Starts the Catalog Service gRPC server on port 50051'

    def handle(self, *args, **options):
        server_cert_path = os.path.join(KEYS_DIR, "grpc_server.crt")
        server_key_path = os.path.join(KEYS_DIR, "grpc_server.key")
        ca_cert_path = os.path.join(KEYS_DIR, "grpc_ca.crt")

        server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=10))
        add_ProductServiceServicer_to_server(ProductService(), server)

        if os.path.exists(server_cert_path) and os.path.exists(server_key_path) and os.path.exists(ca_cert_path):
            server_cert = open(server_cert_path, "rb").read()
            server_key = open(server_key_path, "rb").read()
            ca_cert = open(ca_cert_path, "rb").read()
            credentials = grpc.ssl_server_credentials(
                [(server_key, server_cert)],
                root_certificates=ca_cert,
                require_client_auth=True,
            )
            server.add_secure_port('[::]:50051', credentials)
            print("[Catalog Service] gRPC Server running on port 50051 with mTLS...")
        else:
            server.add_insecure_port('[::]:50051')
            print("[Catalog Service] gRPC Server running on port 50051 (insecure fallback)...")

        server.start()
        server.wait_for_termination()
