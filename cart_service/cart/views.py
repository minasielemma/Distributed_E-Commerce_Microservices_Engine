from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from common.viewsets import FullBaseViewSet
from .models import Cart, CartItem, Wishlist, WishlistItem, ItemRequest
from .serializers import (
    CartSerializer, CartItemSerializer,
    WishlistSerializer, WishlistItemSerializer,
    ItemRequestSerializer, ItemRequestStatusUpdateSerializer
)
import os
import json
import logging
import uuid
from django.conf import settings

try:
    from kafka import KafkaProducer
except ImportError:
    try:
        from kafka_ng import KafkaProducer
    except ImportError:
        KafkaProducer = None

logger = logging.getLogger(__name__)

def publish_kafka_event(event_type, payload):
    if not KafkaProducer:
        logger.warning("KafkaProducer unavailable in cart_service")
        return False

    bootstrap_servers = getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092'))
    event_id = str(uuid.uuid4())
    event_data = {
        'event_id': event_id,
        'event_type': event_type,
        'payload': payload,
    }
    try:
        producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            request_timeout_ms=3000
        )
        producer.send('ecommerce-events', value=event_data)
        producer.flush()
        producer.close()
        logger.info(f"Published {event_type} event {event_id} to Kafka")
        return True
    except Exception as e:
        logger.error(f"Failed publishing {event_type} to Kafka: {e}")
        return False

class CartViewSet(FullBaseViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = CartSerializer
    queryset = Cart.objects.prefetch_related('items').all()

    def get_queryset(self):
        user_id = self.request.user.id
        return Cart.objects.prefetch_related('items').filter(user_id=user_id, status='ACTIVE').order_by('-id')

    def perform_create(self, serializer):
        user_id = self.request.user.id
        tenant_id = getattr(self.request.user, 'tenant_id', None)
        serializer.save(user_id=user_id, tenant_id=tenant_id)

    def _get_cart_for_user(self, request, pk=None):
        if pk:
            try:
                return self.get_object()
            except Exception:
                pass
        cart = Cart.objects.filter(user_id=request.user.id, status='ACTIVE').first()
        if not cart:
            cart = Cart.objects.create(
                user_id=request.user.id,
                tenant_id=getattr(request.user, 'tenant_id', None)
            )
        return cart

    @action(detail=False, methods=['post'], url_path='add-item')
    def add_item(self, request, pk=None):
        cart = self._get_cart_for_user(request, pk)
        serializer = CartItemSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        product_id = serializer.validated_data.get('product_id')
        variant_id = serializer.validated_data.get('variant_id') or None
        quantity = serializer.validated_data.get('quantity', 1)

        # Enforce Self-Purchase Prevention
        user_tenant_id = str(getattr(request.user, 'tenant_id', '') or '')
        token_claims = getattr(request.user, 'token', {}) if hasattr(request.user, 'token') else {}
        owned_tenant_ids = set([str(t) for t in token_claims.get('owned_tenant_ids', []) if t])
        if user_tenant_id:
            owned_tenant_ids.add(user_tenant_id)

        if owned_tenant_ids and product_id:
            try:
                from cart.grpc_client import get_catalog_product
                prod_resp = get_catalog_product(product_id)
                if prod_resp and prod_resp.found:
                    prod_tenant = str(prod_resp.tenant_id or '')
                    if prod_tenant and prod_tenant in owned_tenant_ids:
                        return Response(
                            {'error': 'Self-purchase prohibited: You cannot purchase products from a shop you own or manage.'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
            except Exception as e:
                logger.warning(f"Could not verify product ownership during cart add_item: {e}")
        
        # Check if same product+variant combo already exists
        existing_item = CartItem.objects.filter(
            cart=cart, product_id=product_id, variant_id=variant_id
        ).first()
        if existing_item:
            existing_item.quantity += quantity
            existing_item.save()
            publish_kafka_event('cart.item_added', {
                'user_id': str(request.user.id),
                'product_id': str(product_id),
                'tenant_id': str(getattr(request.user, 'tenant_id', '')) if getattr(request.user, 'tenant_id', None) else None,
                'quantity': quantity
            })
            return Response(CartItemSerializer(existing_item).data, status=status.HTTP_200_OK)
            
        serializer.save(cart=cart)
        publish_kafka_event('cart.item_added', {
            'user_id': str(request.user.id),
            'product_id': str(product_id),
            'tenant_id': str(getattr(request.user, 'tenant_id', '')) if getattr(request.user, 'tenant_id', None) else None,
            'quantity': quantity
        })
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='remove-item')
    def remove_item(self, request, pk=None):
        cart = self._get_cart_for_user(request, pk)
        item_id = request.data.get('item_id')
        CartItem.objects.filter(cart=cart, id=item_id).delete()
        return Response({'status': 'item removed'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='update-item')
    def update_item(self, request, pk=None):
        cart = self._get_cart_for_user(request, pk)
        item_id = request.data.get('item_id')
        quantity = request.data.get('quantity')
        
        try:
            item = CartItem.objects.get(cart=cart, id=item_id)
            if int(quantity) > 0:
                item.quantity = int(quantity)
                item.save()
                return Response({'status': 'item updated'}, status=status.HTTP_200_OK)
            else:
                item.delete()
                return Response({'status': 'item removed'}, status=status.HTTP_200_OK)
        except CartItem.DoesNotExist:
            return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post', 'delete'], url_path='clear')
    def clear_cart(self, request, pk=None):
        cart = self._get_cart_for_user(request, pk)
        cart.items.all().delete()
        cart.coupon_code = None
        cart.discount_amount = 0
        cart.save()
        return Response({'status': 'cart cleared', 'message': 'All items removed from cart'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='apply-coupon')
    def apply_coupon(self, request, pk=None):
        cart = self._get_cart_for_user(request, pk)
        code = request.data.get('coupon_code')
        if not code:
            return Response({'error': 'Coupon code is required'}, status=status.HTTP_400_BAD_REQUEST)

        import os, urllib.request, json
        discount_type = 'PERCENTAGE'
        discount_value = 10.0 if code.upper() == 'SAVE10' else 0.0

        try:
            from cart.grpc_client import validate_coupon_grpc
            c_resp = validate_coupon_grpc(code)
            if c_resp and c_resp.is_valid:
                discount_value = float(c_resp.discount_amount)
        except Exception:
            pass

        from decimal import Decimal
        subtotal = cart.subtotal()
        if discount_type == 'PERCENTAGE':
            disc_amount = (subtotal * Decimal(str(discount_value))) / Decimal('100.0')
        else:
            disc_amount = min(subtotal, Decimal(str(discount_value)))

        cart.coupon_code = code.upper()
        cart.discount_amount = round(disc_amount, 2)
        cart.save()

        serializer = self.get_serializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)


class WishlistViewSet(FullBaseViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = WishlistSerializer
    queryset = Wishlist.objects.prefetch_related('items').all()

    def get_queryset(self):
        user_id = self.request.user.id
        return Wishlist.objects.prefetch_related('items').filter(user_id=user_id).order_by('-id')

    def perform_create(self, serializer):
        user_id = self.request.user.id
        tenant_id = getattr(self.request.user, 'tenant_id', None)
        serializer.save(user_id=user_id, tenant_id=tenant_id)

    def _get_wishlist_for_user(self, request, pk=None):
        if pk:
            try:
                return self.get_object()
            except Exception:
                pass
        wishlist, _ = Wishlist.objects.get_or_create(
            user_id=request.user.id,
            defaults={'tenant_id': getattr(request.user, 'tenant_id', None)}
        )
        return wishlist

    @action(detail=False, methods=['post'], url_path='add-item')
    def add_item(self, request, pk=None):
        wishlist = self._get_wishlist_for_user(request, pk)
        serializer = WishlistItemSerializer(data=request.data)
        if serializer.is_valid():
            item = serializer.save(wishlist=wishlist)
            product_id = request.data.get('product_id') or getattr(item, 'product_id', None)
            publish_kafka_event('wishlist.item_added', {
                'user_id': str(request.user.id),
                'product_id': str(product_id),
                'tenant_id': str(getattr(request.user, 'tenant_id', '')) if getattr(request.user, 'tenant_id', None) else None
            })
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='remove-item')
    def remove_item(self, request, pk=None):
        wishlist = self._get_wishlist_for_user(request, pk)
        item_id = request.data.get('item_id')
        WishlistItem.objects.filter(wishlist=wishlist, id=item_id).delete()
        return Response({'status': 'item removed'}, status=status.HTTP_200_OK)

from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 100

def send_internal_http_post(url, payload_dict, timeout=3):
    import json
    import urllib.request
    try:
        data = json.dumps(payload_dict).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                'Content-Type': 'application/json',
                'X-Service-Token': 'internal'
            }
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status
    except Exception as e:
        print(f"[cart_service] Internal POST error: {e}")
        return None

class ItemRequestViewSet(FullBaseViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ItemRequestSerializer
    pagination_class = StandardResultsSetPagination
    queryset = ItemRequest.objects.all()

    def get_queryset(self):
        user = self.request.user
        role = str(getattr(user, 'role', '')).upper()
        query_params = getattr(self.request, 'query_params', getattr(self.request, 'GET', {}))
        param_tenant = query_params.get('tenant_id') if query_params else None
        scope = query_params.get('scope') if query_params else None
        user_tenant = getattr(user, 'tenant_id', None)

        is_super = getattr(user, 'is_platform_admin', False) or role in ['PLATFORM_ADMIN', 'SUPERADMIN'] or getattr(user, 'is_superuser', False)
        is_staff_or_owner = role in ['STORE_OWNER', 'SHOP_OWNER', 'SHOP_ADMIN', 'VENDOR', 'DEALER'] or is_super

        # 1. Shop Management Mode (When scope='shop' OR when performing detail/update actions by staff/owner)
        if scope == 'shop' or (getattr(self, 'action', None) in ['update_status', 'retrieve', 'update', 'partial_update', 'destroy'] and is_staff_or_owner):
            if is_super:
                if param_tenant:
                    return ItemRequest.objects.filter(tenant_id=param_tenant).order_by('-created_at')
                return ItemRequest.objects.all().order_by('-created_at')
            if user_tenant:
                return ItemRequest.objects.filter(tenant_id=user_tenant).order_by('-created_at')
            return ItemRequest.objects.none()

        # 2. Platform Super Admin fallback with explicit tenant_id filter
        if is_super and param_tenant:
            return ItemRequest.objects.filter(tenant_id=param_tenant).order_by('-created_at')

        # 3. Customer / Personal Mode (Default for storefront listing): ALWAYS filter strictly by user_id = user.id
        qs = ItemRequest.objects.filter(user_id=user.id).order_by('-created_at')
        if param_tenant:
            qs = qs.filter(tenant_id=param_tenant)
        return qs


    def perform_create(self, serializer):
        user_id = self.request.user.id
        payload_tenant = serializer.validated_data.get('tenant_id') or self.request.data.get('tenant_id')
        tenant_id = payload_tenant or getattr(self.request.user, 'tenant_id', None)

        item_req = serializer.save(user_id=user_id, tenant_id=tenant_id)

        if tenant_id:
            from cart.grpc_client import send_notification_grpc
            send_notification_grpc(
                tenant_id=str(tenant_id),
                title=f"New Special Product Request: {item_req.product_name}",
                message=f"A customer submitted a product request: '{item_req.product_name}' (Qty: {item_req.quantity}).",
                notification_type='ITEM_REQUEST'
            )

    @action(detail=True, methods=['post', 'patch'], url_path='update-status')
    def update_status(self, request, pk=None):
        item_request = self.get_object()
        user = request.user
        role = str(getattr(user, 'role', '')).upper()
        user_tenant = getattr(user, 'tenant_id', None)

        is_admin = role in ['ADMIN', 'SUPERADMIN', 'PLATFORM_ADMIN'] or getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False)
        is_owner = bool(user_tenant and item_request.tenant_id and str(user_tenant) == str(item_request.tenant_id))
        if not (is_admin or is_owner):
            return Response({'error': 'Not authorized to update this item request.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = ItemRequestStatusUpdateSerializer(item_request, data=request.data, partial=True)
        if serializer.is_valid():
            updated = serializer.save()
            from cart.grpc_client import send_notification_grpc
            send_notification_grpc(
                recipient_id=str(updated.user_id),
                title=f"Item Request Update: {updated.product_name}",
                message=f"Your product request status was updated to {updated.status}." + (f" Note: {updated.admin_response}" if updated.admin_response else ""),
                notification_type='ITEM_REQUEST'
            )

            return Response(ItemRequestSerializer(updated).data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        qs = self.get_queryset()
        return Response({
            'total': qs.count(),
            'pending': qs.filter(status='PENDING').count(),
            'approved': qs.filter(status='APPROVED').count(),
            'rejected': qs.filter(status='REJECTED').count(),
            'fulfilled': qs.filter(status='FULFILLED').count(),
        }, status=status.HTTP_200_OK)

