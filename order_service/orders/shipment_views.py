import logging
from datetime import datetime
from django.db import transaction
from django.utils import timezone
from rest_framework import views, permissions, status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from .models import Order, Shipping, StatusHistory, OutboxEvent
from .serializers import (
    ShippingSerializer,
    ShipmentCreateSerializer,
    ShipmentStatusUpdateSerializer,
    StatusHistorySerializer,
)

logger = logging.getLogger(__name__)


class TrackingRateThrottle(AnonRateThrottle):
    rate = '20/minute'


class OrderShipmentListView(views.APIView):
    """List or create shipments for a specific order."""
    permission_classes = (permissions.IsAuthenticated,)

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

        if request.user and request.user.is_authenticated:
            user_id = str(request.user.id)
            tenant_id = str(getattr(request.user, 'tenant_id', ''))
            role = str(getattr(request.user, 'role', '')).upper()

            is_customer = str(order.customer_id) == user_id
            is_owner = str(order.tenant_id) == tenant_id or role in ['ADMIN', 'SUPERADMIN', 'PLATFORM_ADMIN', 'STORE_OWNER', 'VENDOR', 'DEALER']
            # Allow authenticated access if customer or owner or if querying tracking
            if not (is_customer or is_owner):
                pass  # Fall through to allow viewing order shipment tracking status

        shipments = order.shipments.all()
        return Response(ShippingSerializer(shipments, many=True).data)

    def post(self, request, order_id):
        """Create a new shipment for an order (Store Owner / Admin only)."""
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

        tenant_id = str(getattr(request.user, 'tenant_id', ''))
        role = str(getattr(request.user, 'role', '')).upper()
        if str(order.tenant_id) != tenant_id and role not in ['ADMIN', 'SUPERADMIN']:
            return Response({'error': 'Not authorized for this store order'}, status=status.HTTP_403_FORBIDDEN)

        # Rule: Unpaid orders (PENDING or FAILED) cannot be shipped
        if order.status in ['PENDING', 'FAILED', 'CANCELLED']:
            return Response({'error': f"Unpaid order {order.id} cannot be shipped. Current status is '{order.status}'. Order must be PAID before shipping."}, status=status.HTTP_400_BAD_REQUEST)

        data = request.data.copy()
        data['order'] = str(order.id)

        # Pre-fill address if not provided
        if not data.get('full_name') and order.shipping_address:
            addr = order.shipping_address
            data.setdefault('full_name', addr.get('full_name', 'Customer'))
            data.setdefault('contact_phone', addr.get('phone', ''))
            data.setdefault('address_line_1', addr.get('address_line_1', ''))
            data.setdefault('address_line_2', addr.get('address_line_2', ''))
            data.setdefault('city', addr.get('city', ''))
            data.setdefault('state', addr.get('state', ''))
            data.setdefault('postcode', addr.get('postal_code') or addr.get('postcode', '00000'))
            data.setdefault('country', addr.get('country', 'USA'))

        serializer = ShipmentCreateSerializer(data=data)
        if serializer.is_valid():
            with transaction.atomic():
                shipment = serializer.save()
                shipment_status = shipment.status

                if shipment_status == 'SHIPPED' and not shipment.shipped_at:
                    shipment.shipped_at = timezone.now()
                    shipment.save(update_fields=['shipped_at'])

                # Log status history
                StatusHistory.objects.create(
                    entity_type='shipping',
                    entity_id=shipment.id,
                    from_status='',
                    to_status=shipment.status,
                    changed_by=request.user.id,
                    notes=f"Shipment created with carrier {shipment.carrier}"
                )

                # Create outbox event
                OutboxEvent.objects.create(
                    event_type='shipment.created',
                    payload={
                        'shipment_id': str(shipment.id),
                        'order_id': str(order.id),
                        'customer_id': str(order.customer_id),
                        'tenant_id': str(order.tenant_id),
                        'tracking_code': shipment.tracking_code,
                        'carrier': shipment.carrier,
                        'status': shipment.status,
                    }
                )

                # Update order status to SHIPPED if applicable using State Machine
                if shipment.status in ['SHIPPED', 'IN_TRANSIT', 'OUT_FOR_DELIVERY'] and order.status != 'SHIPPED':
                    from orders.state_machine import OrderStateMachine
                    if OrderStateMachine.can_transition(order.status, 'SHIPPED'):
                        old_order_status = order.status
                        OrderStateMachine.transition(order, 'SHIPPED')
                        StatusHistory.objects.create(
                            entity_type='order',
                            entity_id=order.id,
                            from_status=old_order_status,
                            to_status='SHIPPED',
                            changed_by=request.user.id,
                            notes=f"Order marked SHIPPED via shipment {shipment.tracking_code}"
                        )


            return Response(ShippingSerializer(shipment).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShipmentDetailView(views.APIView):
    """Retrieve or update a specific shipment."""
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, pk):
        try:
            shipment = Shipping.objects.get(id=pk)
        except Shipping.DoesNotExist:
            return Response({'error': 'Shipment not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response(ShippingSerializer(shipment).data)

    def patch(self, request, pk):
        try:
            shipment = Shipping.objects.get(id=pk)
        except Shipping.DoesNotExist:
            return Response({'error': 'Shipment not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ShippingSerializer(shipment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdateShipmentStatusView(views.APIView):
    """Store Owner action to update shipment status and trigger event workflow."""
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, pk):
        try:
            shipment = Shipping.objects.get(id=pk)
        except Shipping.DoesNotExist:
            return Response({'error': 'Shipment not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ShipmentStatusUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        new_status = serializer.validated_data['status']
        notes = serializer.validated_data.get('notes', '')
        old_status = shipment.status

        with transaction.atomic():
            shipment.status = new_status
            if notes:
                shipment.notes = notes

            if serializer.validated_data.get('carrier'):
                shipment.carrier = serializer.validated_data['carrier']
            if serializer.validated_data.get('tracking_code'):
                shipment.tracking_code = serializer.validated_data['tracking_code']
            if serializer.validated_data.get('estimated_delivery_date'):
                shipment.estimated_delivery_date = serializer.validated_data['estimated_delivery_date']

            if new_status == 'SHIPPED' and not shipment.shipped_at:
                shipment.shipped_at = timezone.now()
            elif new_status == 'DELIVERED' and not shipment.delivered_at:
                shipment.delivered_at = timezone.now()

            shipment.save()

            # Record audit trail
            StatusHistory.objects.create(
                entity_type='shipping',
                entity_id=shipment.id,
                from_status=old_status,
                to_status=new_status,
                changed_by=request.user.id,
                notes=notes or f"Shipment status updated from {old_status} to {new_status}"
            )

            # Check order status auto-progression
            if shipment.order:
                order = shipment.order
                all_shipments = order.shipments.all()
                all_delivered = all_shipments.exists() and all(s.status == 'DELIVERED' for s in all_shipments)
                any_shipped = any(s.status in ['SHIPPED', 'IN_TRANSIT', 'OUT_FOR_DELIVERY', 'DELIVERED'] for s in all_shipments)

                if all_delivered and order.status != 'DELIVERED':
                    from orders.state_machine import OrderStateMachine
                    if OrderStateMachine.can_transition(order.status, 'DELIVERED'):
                        prev_order_status = order.status
                        OrderStateMachine.transition(order, 'DELIVERED')
                        StatusHistory.objects.create(
                            entity_type='order',
                            entity_id=order.id,
                            from_status=prev_order_status,
                            to_status='DELIVERED',
                            changed_by=request.user.id,
                            notes='Order auto-marked DELIVERED as all shipments completed'
                        )
                elif any_shipped and order.status != 'SHIPPED':
                    from orders.state_machine import OrderStateMachine
                    if OrderStateMachine.can_transition(order.status, 'SHIPPED'):
                        prev_order_status = order.status
                        OrderStateMachine.transition(order, 'SHIPPED')
                        StatusHistory.objects.create(
                            entity_type='order',
                            entity_id=order.id,
                            from_status=prev_order_status,
                            to_status='SHIPPED',
                            changed_by=request.user.id,
                            notes='Order auto-marked SHIPPED'
                        )


            # Create outbox event for Kafka and notifications
            OutboxEvent.objects.create(
                event_type='shipment.status_changed',
                payload={
                    'shipment_id': str(shipment.id),
                    'order_id': str(shipment.order.id) if shipment.order else None,
                    'customer_id': str(shipment.order.customer_id) if shipment.order else None,
                    'tenant_id': str(shipment.order.tenant_id) if shipment.order else None,
                    'tracking_code': shipment.tracking_code,
                    'carrier': shipment.carrier,
                    'old_status': old_status,
                    'new_status': new_status,
                    'notes': notes,
                }
            )

        return Response(ShippingSerializer(shipment).data, status=status.HTTP_200_OK)


class ShipmentHistoryView(views.APIView):
    """Retrieve audit history for a shipment or order."""
    permission_classes = (permissions.AllowAny,)

    def get(self, request, pk):
        # Query by entity_id
        logs = StatusHistory.objects.filter(entity_id=pk).order_by('-created_at')
        return Response(StatusHistorySerializer(logs, many=True).data)


class PublicTrackingView(views.APIView):
    """Public endpoint to track package by tracking code."""
    permission_classes = (permissions.AllowAny,)
    throttle_classes = [TrackingRateThrottle]

    def get(self, request, tracking_code):
        try:
            shipment = Shipping.objects.select_related('order').get(tracking_code__iexact=tracking_code)
        except Shipping.DoesNotExist:
            return Response({'error': 'Invalid or unrecognised tracking code.'}, status=status.HTTP_404_NOT_FOUND)

        history = StatusHistory.objects.filter(entity_type='shipping', entity_id=shipment.id).order_by('created_at')

        data = ShippingSerializer(shipment).data
        data['history'] = StatusHistorySerializer(history, many=True).data
        return Response(data)
