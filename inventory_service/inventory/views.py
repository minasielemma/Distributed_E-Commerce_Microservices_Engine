from uuid import UUID
from django.db import transaction
from rest_framework import viewsets, permissions, status, generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Warehouse, InventoryItem, StockMovement
from .serializers import (
    WarehouseSerializer,
    InventoryItemSerializer,
    ReserveStockSerializer,
    StockMovementSerializer
)

def _is_platform_admin(user):
    if not user or not user.is_authenticated:
        return False
    if getattr(user, 'is_platform_admin', False) is True:
        return True
    role = str(getattr(user, 'role', '')).upper()
    return (
        role in ['PLATFORM_ADMIN', 'SUPERADMIN', 'PLATFORM_SUPER_ADMIN']
        or getattr(user, 'is_superuser', False)
    )

def get_tenant_id_from_request(request):
    if not request.user or not request.user.is_authenticated:
        return None
    
    # 1. Non-admin store staff: strictly use validated token tenant_id
    if not _is_platform_admin(request.user):
        token_tenant_id = getattr(request.user, 'tenant_id', None)
        if token_tenant_id:
            try:
                return UUID(str(token_tenant_id))
            except Exception:
                return None
        return None

    # 2. Verified Platform Admins can optionally specify a target tenant via header/query param
    header_tenant = request.META.get('HTTP_X_TENANT_ID') or request.headers.get('X-Tenant-ID') or request.query_params.get('tenant_id')
    if header_tenant:
        try:
            return UUID(str(header_tenant))
        except Exception:
            pass
    token_tenant_id = getattr(request.user, 'tenant_id', None)
    if token_tenant_id:
        try:
            return UUID(str(token_tenant_id))
        except Exception:
            pass
    return None


def _has_service_token(request):
    return bool(
        request.META.get('HTTP_X_SERVICE_TOKEN')
        or request.headers.get('X-Service-Token')
    )

from rest_framework.decorators import action

class WarehouseViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WarehouseSerializer

    def get_queryset(self):
        user = self.request.user
        tenant_id = get_tenant_id_from_request(self.request)
        if _is_platform_admin(user):
            if tenant_id:
                return Warehouse.objects.filter(tenant_id=tenant_id).order_by('-id')
            return Warehouse.objects.all().order_by('-id')
        if tenant_id:
            return Warehouse.objects.filter(tenant_id=tenant_id).order_by('-id')
        return Warehouse.objects.none()

    def perform_create(self, serializer):
        tenant_id = get_tenant_id_from_request(self.request)
        serializer.save(tenant_id=tenant_id)

class InventoryItemViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = InventoryItemSerializer

    def get_permissions(self):
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        tenant_id = get_tenant_id_from_request(self.request)
        product_id = self.request.query_params.get('product_id')

        if _is_platform_admin(user):
            qs = InventoryItem.objects.select_related('warehouse').all()
            if tenant_id:
                qs = qs.filter(tenant_id=tenant_id)
            if product_id:
                qs = qs.filter(product_id=product_id)
            return qs.order_by('-id')

        if tenant_id:
            qs = InventoryItem.objects.select_related('warehouse').filter(tenant_id=tenant_id)
            if product_id:
                qs = qs.filter(product_id=product_id)
            return qs.order_by('-id')

        return InventoryItem.objects.none()

    def perform_create(self, serializer):
        tenant_id = get_tenant_id_from_request(self.request)
        serializer.save(tenant_id=tenant_id)


class PublicStockCheckView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        product_id = request.query_params.get('product_id')
        if not product_id:
            return Response({'error': 'product_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            items = InventoryItem.objects.filter(product_id=UUID(str(product_id)))
            total_qty = sum(item.quantity_available for item in items)
            return Response({
                'product_id': str(product_id),
                'in_stock': total_qty > 0,
                'quantity_available': max(total_qty, 0)
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': 'Invalid product_id'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='init-product', permission_classes=[permissions.AllowAny])
    def init_product(self, request):
        if not _has_service_token(request) and not (request.user and request.user.is_authenticated):
            return Response({'error': 'Service token or authentication required'}, status=status.HTTP_403_FORBIDDEN)
        product_id = request.data.get('product_id')
        if not product_id:
            return Response({'error': 'product_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        tenant_id = request.data.get('tenant_id')
        if not tenant_id:
            tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            tenant_id = UUID('00000000-0000-0000-0000-000000000000')
        else:
            tenant_id = UUID(str(tenant_id))

        qty = int(request.data.get('quantity_available', 100))
        reorder_lvl = int(request.data.get('reorder_level', 10))

        warehouse, _ = Warehouse.objects.get_or_create(
            tenant_id=tenant_id,
            code='MAIN',
            defaults={
                'name': 'Main Warehouse',
                'address': 'Primary Fulfillment Center'
            }
        )

        item, created = InventoryItem.objects.get_or_create(
            tenant_id=tenant_id,
            product_id=UUID(str(product_id)),
            warehouse=warehouse,
            defaults={
                'quantity_available': qty,
                'reorder_level': reorder_lvl
            }
        )

        if not created:
            item.quantity_available = qty
            item.reorder_level = reorder_lvl
            item.save()

        serializer = self.get_serializer(item)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='add-stock', permission_classes=[permissions.IsAuthenticated])
    def add_stock(self, request):
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 0))
        reference_id = request.data.get('reference_id', f'RESTOCK-{product_id}')

        if not product_id:
            return Response({'error': 'product_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        if quantity <= 0:
            return Response({'error': 'quantity must be greater than 0'}, status=status.HTTP_400_BAD_REQUEST)

        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            tenant_id = UUID('00000000-0000-0000-0000-000000000000')

        with transaction.atomic():
            warehouse, _ = Warehouse.objects.get_or_create(
                tenant_id=tenant_id,
                code='MAIN',
                defaults={'name': 'Main Warehouse', 'address': 'Primary Fulfillment Center'}
            )
            item, _ = InventoryItem.objects.get_or_create(
                tenant_id=tenant_id,
                product_id=UUID(str(product_id)),
                warehouse=warehouse,
                defaults={'quantity_available': 0, 'reorder_level': 10}
            )
            item.quantity_available += quantity
            item.save()

            StockMovement.objects.create(
                tenant_id=tenant_id,
                inventory_item=item,
                movement_type='INBOUND',
                quantity=quantity,
                reference_id=reference_id
            )

        serializer = self.get_serializer(item)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ReserveStockView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        if not _has_service_token(request):
            return Response({'error': 'Service token required'}, status=status.HTTP_403_FORBIDDEN)
        serializer = ReserveStockSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        tenant_id = get_tenant_id_from_request(request) or request.data.get('tenant_id')
        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data['quantity']
        reference_id = serializer.validated_data.get('reference_id', '')

        with transaction.atomic():
            qs = InventoryItem.objects.select_for_update().select_related('warehouse').filter(product_id=product_id)
            if tenant_id:
                qs = qs.filter(tenant_id=tenant_id)
            item = qs.first()
            if not item:
                item = InventoryItem.objects.select_for_update().select_related('warehouse').filter(product_id=product_id).first()

            if not item:
                eff_tenant = tenant_id or UUID('00000000-0000-0000-0000-000000000000')
                if isinstance(eff_tenant, str):
                    try:
                        eff_tenant = UUID(eff_tenant)
                    except Exception:
                        eff_tenant = UUID('00000000-0000-0000-0000-000000000000')
                wh, _ = Warehouse.objects.get_or_create(
                    tenant_id=eff_tenant,
                    code='MAIN',
                    defaults={'name': 'Main Warehouse'}
                )
                item, _ = InventoryItem.objects.get_or_create(
                    tenant_id=eff_tenant,
                    product_id=product_id,
                    warehouse=wh,
                    defaults={'quantity_available': 0, 'quantity_reserved': 0}
                )

            if item.quantity_available < quantity:
                return Response({
                    'error': f"Product is out of stock or has insufficient available inventory. Requested: {quantity}, Available: {item.quantity_available}",
                    'requested': quantity,
                    'available': item.quantity_available
                }, status=status.HTTP_400_BAD_REQUEST)

            item.quantity_available -= quantity
            item.quantity_reserved += quantity
            item.save()

            StockMovement.objects.create(
                tenant_id=item.tenant_id,
                inventory_item=item,
                movement_type='RESERVED',
                quantity=quantity,
                reference_id=reference_id
            )

        return Response({
            'message': 'Stock reserved successfully',
            'product_id': str(product_id),
            'quantity_reserved': quantity,
            'remaining_available': item.quantity_available
        }, status=status.HTTP_200_OK)

class ReleaseStockView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        if not _has_service_token(request):
            return Response({'error': 'Service token required'}, status=status.HTTP_403_FORBIDDEN)
        serializer = ReserveStockSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        tenant_id = get_tenant_id_from_request(request) or request.data.get('tenant_id')
        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data['quantity']
        reference_id = serializer.validated_data.get('reference_id', '')

        with transaction.atomic():
            qs = InventoryItem.objects.select_for_update().select_related('warehouse').filter(product_id=product_id)
            if tenant_id:
                qs = qs.filter(tenant_id=tenant_id)
            item = qs.first()
            if not item:
                item = InventoryItem.objects.select_for_update().select_related('warehouse').filter(product_id=product_id).first()

            if not item:
                eff_tenant = tenant_id or UUID('00000000-0000-0000-0000-000000000000')
                if isinstance(eff_tenant, str):
                    try:
                        eff_tenant = UUID(eff_tenant)
                    except Exception:
                        eff_tenant = UUID('00000000-0000-0000-0000-000000000000')
                wh, _ = Warehouse.objects.get_or_create(
                    tenant_id=eff_tenant,
                    code='MAIN',
                    defaults={'name': 'Main Warehouse'}
                )
                item, _ = InventoryItem.objects.get_or_create(
                    tenant_id=eff_tenant,
                    product_id=product_id,
                    warehouse=wh,
                    defaults={'quantity_available': 0, 'quantity_reserved': 0}
                )

            release_qty = min(quantity, item.quantity_reserved)
            item.quantity_reserved -= release_qty
            item.quantity_available += release_qty
            item.save()

            StockMovement.objects.create(
                tenant_id=item.tenant_id,
                inventory_item=item,
                movement_type='RELEASED',
                quantity=release_qty,
                reference_id=reference_id
            )

        return Response({
            'message': 'Stock released successfully',
            'product_id': str(product_id),
            'quantity_released': release_qty,
            'current_available': item.quantity_available
        }, status=status.HTTP_200_OK)

class CommitStockView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        if not _has_service_token(request):
            return Response({'error': 'Service token required'}, status=status.HTTP_403_FORBIDDEN)
        serializer = ReserveStockSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        tenant_id = get_tenant_id_from_request(request) or request.data.get('tenant_id')
        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data['quantity']
        reference_id = serializer.validated_data.get('reference_id', '')

        with transaction.atomic():
            qs = InventoryItem.objects.select_for_update().select_related('warehouse').filter(product_id=product_id)
            if tenant_id:
                qs = qs.filter(tenant_id=tenant_id)
            item = qs.first()
            if not item:
                item = InventoryItem.objects.select_for_update().select_related('warehouse').filter(product_id=product_id).first()

            if not item:
                eff_tenant = tenant_id or UUID('00000000-0000-0000-0000-000000000000')
                if isinstance(eff_tenant, str):
                    try:
                        eff_tenant = UUID(eff_tenant)
                    except Exception:
                        eff_tenant = UUID('00000000-0000-0000-0000-000000000000')
                wh, _ = Warehouse.objects.get_or_create(
                    tenant_id=eff_tenant,
                    code='MAIN',
                    defaults={'name': 'Main Warehouse'}
                )
                item, _ = InventoryItem.objects.get_or_create(
                    tenant_id=eff_tenant,
                    product_id=product_id,
                    warehouse=wh,
                    defaults={'quantity_available': 0, 'quantity_reserved': 0}
                )

            if item.quantity_reserved >= quantity:
                item.quantity_reserved -= quantity
                commit_qty = quantity
            else:
                commit_qty = quantity
                remaining = quantity - item.quantity_reserved
                item.quantity_reserved = 0
                item.quantity_available = max(0, item.quantity_available - remaining)
            item.save()

            StockMovement.objects.create(
                tenant_id=item.tenant_id,
                inventory_item=item,
                movement_type='OUTBOUND',
                quantity=commit_qty,
                reference_id=reference_id
            )

        return Response({
            'message': 'Stock committed successfully',
            'product_id': str(product_id),
            'quantity_committed': commit_qty
        }, status=status.HTTP_200_OK)

class StockMovementListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = StockMovementSerializer

    def get_queryset(self):
        user = self.request.user
        tenant_id = get_tenant_id_from_request(self.request)
        if _is_platform_admin(user):
            if tenant_id:
                return StockMovement.objects.select_related('inventory_item', 'inventory_item__warehouse').filter(tenant_id=tenant_id).order_by('-created_at')
            return StockMovement.objects.select_related('inventory_item', 'inventory_item__warehouse').all().order_by('-created_at')
        if tenant_id:
            return StockMovement.objects.select_related('inventory_item', 'inventory_item__warehouse').filter(tenant_id=tenant_id).order_by('-created_at')
        return StockMovement.objects.none()
