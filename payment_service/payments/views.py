import uuid
import json
import logging
from decimal import Decimal
from django.db import transaction
from django.conf import settings
from django.http import HttpResponseRedirect
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Payment
from .serializers import CreateCheckoutSerializer, PaymentSerializer
from .polar_provider import PolarPaymentProvider
from .utils import verify_service_token
try:
    from kafka import KafkaProducer
except ImportError:
    from kafka_ng import KafkaProducer
logger = logging.getLogger(__name__)
import requests

def post_order_payment_journal_entry(payment):
    try:
        from .utils import make_service_token
        service_token = make_service_token()
        from payments.grpc_client import record_ledger_payment_grpc
        record_ledger_payment_grpc(tenant_id_str=str(payment.tenant_id) if payment.tenant_id else '', order_id_str=str(payment.order_id), payment_id_str=str(payment.id), amount_float=float(payment.amount))
    except Exception as e:
        logger.warning(f'Could not trigger direct finance ledger recording: {e}')

class CreateCheckoutSessionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not verify_service_token(request):
            return Response({'error': 'Invalid or missing service token'}, status=status.HTTP_403_FORBIDDEN)
        serializer = CreateCheckoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        order_id = serializer.validated_data['order_id']
        amount = serializer.validated_data['amount']
        tenant_id = serializer.validated_data.get('tenant_id') or getattr(request.user, 'tenant_id', None)
        customer_id = request.user.id
        discount_code = request.data.get('discount_code')
        discount_amount = request.data.get('discount_amount', '0.00')
        existing_payment = Payment.objects.filter(order_id=order_id, status='PENDING').first()
        if existing_payment and existing_payment.polar_checkout_url:
            return Response({'message': 'Existing checkout session retrieved', 'payment': PaymentSerializer(existing_payment).data, 'checkout_url': existing_payment.polar_checkout_url}, status=status.HTTP_200_OK)
        catalog_product_id = request.data.get('product_id')
        polar_product_id = request.data.get('polar_product_id')
        product_name = request.data.get('product_name')

        provider = PolarPaymentProvider()
        session_info = provider.create_checkout_session(order_id, customer_id, amount, catalog_product_id=catalog_product_id, polar_product_id=polar_product_id, product_name=product_name)

        checkout_base = get_polar_checkout_base_url()
        checkout_url = session_info.get('checkout_url') or f"{checkout_base}/polar_chk_{uuid.uuid4().hex[:12]}"
        checkout_id = session_info.get('checkout_id') or f"polar_chk_{uuid.uuid4().hex[:12]}"

        with transaction.atomic():
            payment, created = Payment.objects.select_for_update().get_or_create(
                order_id=order_id,
                defaults={
                    'tenant_id': tenant_id,
                    'customer_id': customer_id,
                    'amount': amount,
                    'discount_code': discount_code,
                    'discount_amount': discount_amount,
                    'provider': 'POLAR',
                    'status': 'PENDING',
                    'polar_checkout_id': checkout_id,
                    'polar_checkout_url': checkout_url
                }
            )
            if not created:
                payment.polar_checkout_id = checkout_id
                payment.polar_checkout_url = checkout_url
                payment.amount = amount
                payment.save()
        return Response({'message': 'Polar Checkout session created successfully', 'payment': PaymentSerializer(payment).data, 'checkout_url': checkout_url}, status=status.HTTP_201_CREATED)

class ConfirmPaymentSessionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        order_id = request.data.get('order_id')
        if not order_id:
            return Response({'error': 'order_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            payment = Payment.objects.select_for_update().filter(order_id=order_id).first()
            if payment:
                is_admin = getattr(request.user, 'is_superuser', False) or getattr(request.user, 'is_adminuser', False)
                service_token = request.META.get('HTTP_X_SERVICE_TOKEN') or request.headers.get('X-Service-Token')
                if not is_admin and (not service_token) and (str(payment.customer_id) != str(request.user.id)):
                    return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
            if not payment:
                payment = Payment.objects.create(order_id=order_id, customer_id=request.user.id, tenant_id=getattr(request.user, 'tenant_id', None), amount=Decimal(str(request.data.get('amount') or '10.00')), provider='SIMULATED', status='PAID', polar_checkout_id=f'sim_chk_{uuid.uuid4().hex[:10]}')
            if payment.status == 'PAID':
                return Response({'message': f'Payment for order {order_id} already confirmed (idempotent)', 'payment': PaymentSerializer(payment).data, 'status': 'PAID'}, status=status.HTTP_200_OK)
            payment.status = 'PAID'
            payment.save()
            post_order_payment_journal_entry(payment)
            try:
                from payments.grpc_client import mark_order_paid_grpc
                mark_order_paid_grpc(str(order_id))
            except Exception as e:
                logger.exception(f'Failed to notify order service of paid status: {e}')
                raise Exception('Could not update order status') from e
        if payment.discount_code:
            try:
                from payments.grpc_client import confirm_coupon_grpc
                confirm_coupon_grpc(str(order_id))
            except Exception as coupon_err:
                logger.warning(f'Could not confirm coupon for order {order_id}: {coupon_err}')
        return Response({'message': f'Payment for order {order_id} confirmed and marked as PAID', 'payment': PaymentSerializer(payment).data, 'status': 'PAID'}, status=status.HTTP_200_OK)

class PolarWebhookView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        provider = PolarPaymentProvider()
        sig = request.META.get('HTTP_WEBHOOK_SIGNATURE') or request.META.get('HTTP_X_POLAR_SIGNATURE') or request.META.get('HTTP_POLAR_SIGNATURE') or request.headers.get('webhook-signature') or request.headers.get('x-polar-signature')
        msg_id = request.META.get('HTTP_WEBHOOK_ID') or request.headers.get('webhook-id')
        msg_timestamp = request.META.get('HTTP_WEBHOOK_TIMESTAMP') or request.headers.get('webhook-timestamp')
        if not provider.verify_webhook_signature(request.body, sig, msg_id=msg_id, msg_timestamp=msg_timestamp):
            logger.warning(f"Rejecting Polar webhook from {request.META.get('REMOTE_ADDR')}: Invalid signature")
            return Response({'error': 'Invalid Polar webhook signature'}, status=status.HTTP_401_UNAUTHORIZED)
        data = request.data
        payload_data = data.get('data', {})
        event_type = data.get('type') or data.get('event') or ''
        webhook_status = str(payload_data.get('status') or data.get('status') or '').lower()
        if webhook_status and webhook_status in ['open', 'pending', 'failed', 'cancelled', 'expired']:
            logger.info(f"Polar webhook event '{event_type}' ignored due to status '{webhook_status}'")
            return Response({'status': 'ignored', 'message': f'Event status is {webhook_status}'}, status=status.HTTP_200_OK)
        order_id = payload_data.get('metadata', {}).get('order_id') or payload_data.get('order_id') or data.get('order_id') or payload_data.get('custom_field_data', {}).get('order_id')
        checkout_id = payload_data.get('id') or payload_data.get('checkout_id') or data.get('checkout_id') or data.get('id')
        payment = None
        if order_id:
            payment = Payment.objects.filter(order_id=order_id).first()
        if not payment and checkout_id:
            payment = Payment.objects.filter(polar_checkout_id=checkout_id).first()
        if payment:
            with transaction.atomic():
                payment = Payment.objects.select_for_update().get(pk=payment.pk)
                if payment.status == 'PAID':
                    return Response({'status': 'already_paid', 'message': 'Payment already processed (idempotent)'}, status=status.HTTP_200_OK)
                payment.status = 'PAID'
                payment.save()
                post_order_payment_journal_entry(payment)
                try:
                    producer = KafkaProducer(bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS, value_serializer=lambda v: json.dumps(v).encode('utf-8'))
                    event_payload = {'event_type': 'payment.succeeded', 'payment_id': str(payment.id), 'order_id': str(payment.order_id), 'customer_id': str(payment.customer_id), 'tenant_id': str(payment.tenant_id) if payment.tenant_id else None, 'amount': float(payment.amount), 'discount_code': payment.discount_code, 'discount_amount': float(payment.discount_amount or 0), 'provider': 'POLAR', 'status': 'PAID'}
                    producer.send('ecommerce-events', value=event_payload)
                    producer.flush()
                    logger.info(f'Published payment.succeeded event for order {payment.order_id} to Kafka')
                except Exception as k_err:
                    logger.error(f'Failed to publish Kafka event for order {payment.order_id}: {k_err}')
                    raise Exception('Could not publish payment event to Kafka') from k_err
                try:
                    from payments.grpc_client import mark_order_paid_grpc
                    mark_order_paid_grpc(str(payment.order_id))
                except Exception as ord_err:
                    logger.warning(f'Could not update order status directly in webhook: {ord_err}')
            if payment.discount_code:
                try:
                    from payments.grpc_client import confirm_coupon_grpc
                    confirm_coupon_grpc(str(payment.order_id))
                except Exception as coupon_err:
                    logger.warning(f'Could not confirm coupon for order {payment.order_id}: {coupon_err}')
            return Response({'status': 'PAID', 'message': 'Payment successfully marked as PAID', 'payment_id': str(payment.id), 'order_id': str(payment.order_id)}, status=status.HTTP_200_OK)
        return Response({'status': 'ignored', 'message': 'Webhook received'}, status=status.HTTP_200_OK)

class PaymentListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PaymentSerializer

    def get_queryset(self):
        user = self.request.user
        is_admin = getattr(user, 'is_superuser', False) or getattr(user, 'is_adminuser', False)
        user_tenant = getattr(user, 'tenant_id', None)
        user_role = str(getattr(user, 'role', '') or '').lower()
        if is_admin:
            return Payment.objects.all().order_by('-created_at')
        elif user_tenant or user_role in ['admin', 'vendor', 'tenant_admin', 'owner', 'shop_owner', 'staff']:
            if user_tenant:
                from django.db.models import Q
                return Payment.objects.filter(Q(tenant_id=user_tenant) | Q(tenant_id__isnull=True)).order_by('-created_at')
            return Payment.objects.all().order_by('-created_at')
        return Payment.objects.filter(customer_id=user.id).order_by('-created_at')

class PolarCheckoutView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, payment_id):
        try:
            payment = Payment.objects.filter(pk=payment_id).first()
            if not payment:
                payment = Payment.objects.filter(polar_checkout_id=str(payment_id)).first()
            if not payment:
                payment = Payment.objects.filter(order_id=str(payment_id)).first()
            if not payment:
                return Response({'error': 'Payment session not found'}, status=status.HTTP_404_NOT_FOUND)
            if payment.status != 'PAID':
                with transaction.atomic():
                    payment.status = 'PAID'
                    payment.save()
                    post_order_payment_journal_entry(payment)
                    try:
                        from payments.grpc_client import mark_order_paid_grpc
                        mark_order_paid_grpc(str(payment.order_id))
                    except Exception as ord_err:
                        logger.warning(f'Could not update order status for order {payment.order_id}: {ord_err}')
                    if payment.discount_code:
                        try:
                            from payments.grpc_client import confirm_coupon_grpc
                            confirm_coupon_grpc(str(payment.order_id))
                        except Exception as coupon_err:
                            logger.warning(f'Could not confirm coupon for order {payment.order_id}: {coupon_err}')
            if 'text/html' in request.headers.get('Accept', '') or not request.headers.get('X-Requested-With'):
                return HttpResponseRedirect(f'/checkout/success?order_id={payment.order_id}')
            return Response({'message': 'Simulated Polar checkout completed successfully', 'status': 'PAID', 'payment': PaymentSerializer(payment).data, 'redirect_url': f'/checkout/success?order_id={payment.order_id}'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f'Error handling simulated Polar checkout: {e}')
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, payment_id):
        return self.get(request, payment_id)
