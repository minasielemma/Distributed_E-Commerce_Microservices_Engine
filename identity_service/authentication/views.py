import uuid
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework_simplejwt.views import TokenObtainPairView
from common.viewsets import FullBaseViewSet
from common.permissions import IsPlatformAdmin, IsServiceCall, _is_platform_admin


from django.db.models import Q
from .models import User, Tenant, Subscription, UserProfile, ActivityLog, UserAddress, Notification
from .serializers import (
    RegisterSerializer,
    CustomTokenObtainPairSerializer,
    TenantSerializer,
    UserProfileSerializer,
    ActivityLogSerializer,
    ConfigureSubscriptionSerializer,
    UserAddressSerializer,
    NotificationSerializer
)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

class CreateTenantView(generics.CreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = TenantSerializer

    def perform_create(self, serializer):
        tenant = serializer.save(owner=self.request.user)
        Subscription.objects.create(
            tenant=tenant,
            plan_name=tenant.subscription_tier,
            status='ACTIVE'
        )
        ActivityLog.objects.create(
            tenant_id=tenant.id,
            actor_id=self.request.user.id,
            actor_email=getattr(self.request.user, 'email', ''),
            actor_role=getattr(self.request.user, 'role', 'STORE_OWNER'),
            action="tenant.created",
            resource_type="TENANT",
            resource_id=str(tenant.id),
            status="SUCCESS",
            details={"tenant_id": str(tenant.id), "shop_name": tenant.name, "domain": tenant.domain}
        )

from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class TenantListView(generics.ListAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = TenantSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        scope = self.request.query_params.get('scope')
        search = self.request.query_params.get('search') or self.request.query_params.get('q')

        is_admin = bool(user and user.is_authenticated and (_is_platform_admin(user) or str(getattr(user, 'role', '')).upper() in ['PLATFORM_ADMIN', 'ADMIN', 'SUPER_ADMIN']))

        if is_admin:
            qs = Tenant.objects.all().order_by('-created_at')
        elif scope in ['public', 'active', 'all'] or not user or not user.is_authenticated:
            qs = Tenant.objects.filter(status='ACTIVE').order_by('-created_at')
        else:
            qs = Tenant.objects.filter(owner=user).order_by('-created_at')

        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(domain__icontains=search))

        return qs

    def paginate_queryset(self, queryset):
        fetch_all = self.request.query_params.get('no_page') or self.request.query_params.get('all')
        if fetch_all and str(fetch_all).lower() == 'true':
            return None
        return super().paginate_queryset(queryset)



class AdminConfigureSubscriptionView(generics.UpdateAPIView):
    permission_classes = (IsPlatformAdmin,)
    queryset = Tenant.objects.all()
    serializer_class = ConfigureSubscriptionSerializer

    def perform_update(self, serializer):
        tenant = serializer.save()
        Subscription.objects.update_or_create(
            tenant=tenant,
            defaults={'plan_name': tenant.subscription_tier, 'status': tenant.status}
        )
        ActivityLog.objects.create(
            tenant_id=tenant.id,
            actor_id=self.request.user.id,
            actor_email=getattr(self.request.user, 'email', ''),
            actor_role=getattr(self.request.user, 'role', 'ADMIN'),
            action="admin.subscription_configured",
            resource_type="TENANT",
            resource_id=str(tenant.id),
            status="SUCCESS",
            details={
                "subscription_tier": tenant.subscription_tier,
                "status": tenant.status,
                "has_catalog_access": tenant.has_catalog_access,
                "has_inventory_access": tenant.has_inventory_access,
                "has_finance_access": tenant.has_finance_access,
                "has_payment_access": tenant.has_payment_access,
            }
        )

class UserProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserProfileSerializer

    def get_object(self):
        profile, created = UserProfile.objects.select_related('user').get_or_create(user=self.request.user)
        return profile

    def perform_update(self, serializer):
        profile = serializer.save()
        ActivityLog.objects.create(
            actor_id=self.request.user.id,
            actor_email=getattr(self.request.user, 'email', ''),
            actor_role=getattr(self.request.user, 'role', 'USER'),
            action="user.profile_updated",
            resource_type="USER_PROFILE",
            resource_id=str(profile.id),
            status="SUCCESS",
            details={"phone_number": profile.phone_number, "address": profile.address}
        )

class ActivityLogListView(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ActivityLogSerializer

    def get_queryset(self):
        user = self.request.user
        user_role = str(getattr(user, 'role', '')).upper()
        is_admin = user_role in ['PLATFORM_ADMIN', 'ADMIN', 'SUPER_ADMIN'] or getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False)
        is_owner = user_role in ['STORE_OWNER', 'SHOP_OWNER', 'VENDOR', 'DEALER', 'TENANT_ADMIN', 'OWNER']

        tenant_id = getattr(user, 'tenant_id', None) or self.request.headers.get('X-Tenant-Id')

        if is_admin:
            qs = ActivityLog.objects.all()
            param_tenant = self.request.query_params.get('tenant_id')
            if param_tenant:
                qs = qs.filter(tenant_id=param_tenant)
        elif is_owner and tenant_id:
            from django.db.models import Q
            qs = ActivityLog.objects.filter(Q(tenant_id=tenant_id) | Q(actor_id=user.id))
        else:
            qs = ActivityLog.objects.filter(actor_id=user.id)

        action_filter = self.request.query_params.get('action')
        if action_filter:
            qs = qs.filter(action__icontains=action_filter)

        resource_type = self.request.query_params.get('resource_type')
        if resource_type:
            qs = qs.filter(resource_type=resource_type)

        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        start_date = self.request.query_params.get('start_date')
        if start_date:
            qs = qs.filter(timestamp__gte=start_date)

        end_date = self.request.query_params.get('end_date')
        if end_date:
            qs = qs.filter(timestamp__lte=end_date)

        search = self.request.query_params.get('search')
        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(action__icontains=search) |
                Q(actor_email__icontains=search) |
                Q(resource_type__icontains=search) |
                Q(resource_id__icontains=search)
            )

        return qs.order_by('-timestamp')

class CreateInternalActivityLogView(APIView):
    permission_classes = (IsServiceCall,)

    def post(self, request):
        data = request.data
        action_name = data.get('action')
        if not action_name:
            return Response({'error': 'action is required.'}, status=status.HTTP_400_BAD_REQUEST)

        details = data.get('details', {})
        if isinstance(details, dict):
            for secret_key in ['password', 'token', 'secret', 'credit_card', 'cvv']:
                if secret_key in details:
                    details[secret_key] = '***REDACTED***'

        log_obj = ActivityLog.objects.create(
            tenant_id=data.get('tenant_id') if data.get('tenant_id') != 'None' else None,
            actor_id=data.get('actor_id') if data.get('actor_id') != 'None' else None,
            actor_email=data.get('actor_email', ''),
            actor_role=data.get('actor_role', ''),
            action=action_name,
            resource_type=data.get('resource_type', ''),
            resource_id=str(data.get('resource_id', '')),
            status=data.get('status', 'SUCCESS'),
            ip_address=data.get('ip_address'),
            user_agent=data.get('user_agent', ''),
            details=details,
            changes=data.get('changes', {})
        )
        return Response(ActivityLogSerializer(log_obj).data, status=status.HTTP_201_CREATED)

class UserAddressViewSet(FullBaseViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserAddressSerializer

    def get_queryset(self):
        return UserAddress.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class NotificationViewSet(FullBaseViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

    @action(detail=True, methods=['post'], url_path='read')
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'notification marked as read'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='mark_read')
    def mark_read_alt(self, request, pk=None):
        return self.mark_as_read(request, pk)

    @action(detail=False, methods=['post'], url_path='mark_all_read')
    def mark_all_read(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'status': 'all notifications marked as read'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='create-internal', permission_classes=[IsServiceCall])
    def create_internal(self, request):
        from django.db.models import Q
        user_id = request.data.get('user_id')
        tenant_id = request.data.get('tenant_id')
        title = request.data.get('title')
        message = request.data.get('message')
        notification_type = request.data.get('notification_type', 'SYSTEM')
        metadata = request.data.get('metadata', {})

        if not (title and message and (user_id or tenant_id)):
            return Response({'error': 'title, message, and user_id or tenant_id are required.'}, status=status.HTTP_400_BAD_REQUEST)

        target_users = []
        if user_id:
            target_users = list(User.objects.filter(id=user_id))
        elif tenant_id:
            owners = []
            try:
                tenants = Tenant.objects.filter(Q(id=tenant_id) | Q(domain=tenant_id)).select_related('owner')
                for t in tenants:
                    if t.owner:
                        owners.append(t.owner)
            except Exception:
                pass

            if not owners:
                owners = list(User.objects.filter(role__in=['STORE_OWNER', 'PLATFORM_ADMIN']))

            seen = set()
            for u in owners:
                if u.id not in seen:
                    seen.add(u.id)
                    target_users.append(u)

        if not target_users and not tenant_id:
            return Response({'error': 'No matching user or tenant owner found.'}, status=status.HTTP_404_NOT_FOUND)

        created_notifs = []
        target_user_ids = []
        for u in target_users:
            n = Notification.objects.create(
                user=u,
                title=title,
                message=message,
                notification_type=notification_type,
                metadata=metadata
            )
            created_notifs.append(n)
            target_user_ids.append(str(u.id))

        # Push notification event to Kafka
        try:
            import json, os
            try:
                from kafka import KafkaProducer
            except ImportError:
                from kafka_ng import KafkaProducer

            bootstrap_servers = getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092'))
            producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            event_data = {
                'event_type': 'notification.send',
                'payload': {
                    'recipient_ids': target_user_ids,
                    'tenant_id': str(tenant_id) if tenant_id else None,
                    'title': title,
                    'message': message,
                    'notification_type': notification_type,
                    'metadata': metadata
                }
            }
            producer.send('notifications', event_data)
            producer.flush()
            producer.close()
        except Exception as err:
            print(f"[identity_service] Broadcast Kafka error: {err}")

        first_data = NotificationSerializer(created_notifs[0]).data if created_notifs else {'status': 'queued'}
        return Response(first_data, status=status.HTTP_201_CREATED)


class UserLookupView(APIView):
    """Internal/Authenticated view to look up user(s) by username, UUID, role, or tenant_id."""
    permission_classes = (IsServiceCall,)

    def get(self, request):
        username = request.query_params.get('username')
        user_id = request.query_params.get('user_id')
        search = request.query_params.get('search')
        role = request.query_params.get('role')
        tenant_id = request.query_params.get('tenant_id')

        if role:
            roles = [r.strip().upper() for r in role.split(',')]
            if 'ADMIN' in roles or 'PLATFORM_ADMIN' in roles:
                roles.extend(['PLATFORM_ADMIN', 'ADMIN', 'SUPER_ADMIN'])
            users = User.objects.filter(role__in=roles, is_active=True)
            results = [{
                'id': str(u.id),
                'username': u.username,
                'email': u.email,
                'role': u.role
            } for u in users]
            return Response({'results': results, 'count': len(results)}, status=status.HTTP_200_OK)

        if tenant_id:
            owners = []
            try:
                try:
                    uuid_val = uuid.UUID(str(tenant_id))
                    t_qs = Tenant.objects.filter(id=uuid_val).select_related('owner')
                except (ValueError, TypeError):
                    t_qs = Tenant.objects.filter(domain=tenant_id).select_related('owner')

                for t in t_qs:
                    if t.owner and t.owner.is_active:
                        owners.append(t.owner)
            except Exception:
                pass

            if not owners:
                try:
                    from .models import TenantMembership
                    try:
                        uuid_val = uuid.UUID(str(tenant_id))
                        tm_qs = TenantMembership.objects.filter(tenant_id=uuid_val, is_active=True).select_related('user')
                    except (ValueError, TypeError):
                        tm_qs = TenantMembership.objects.filter(tenant__domain=tenant_id, is_active=True).select_related('user')

                    for tm in tm_qs:
                        if tm.user and tm.user.is_active:
                            owners.append(tm.user)
                except Exception:
                    pass

            if not owners:
                owners = list(User.objects.filter(role__in=['STORE_OWNER', 'SHOP_OWNER', 'TENANT_ADMIN'], is_active=True))

            seen = set()
            results = []
            for u in owners:
                if u.id not in seen:
                    seen.add(u.id)
                    results.append({
                        'id': str(u.id),
                        'username': u.username,
                        'email': u.email,
                        'role': u.role
                    })
            return Response({'results': results, 'count': len(results)}, status=status.HTTP_200_OK)

        qs = User.objects.all()
        if username:
            qs = qs.filter(username__iexact=username)
        elif user_id:
            qs = qs.filter(id=user_id)
        elif search:
            qs = qs.filter(username__icontains=search) | qs.filter(email__icontains=search)
        else:
            return Response({'error': 'Specify username, user_id, search, role, or tenant_id parameter.'}, status=status.HTTP_400_BAD_REQUEST)

        user = qs.first()
        if not user:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'id': str(user.id),
            'username': user.username,
            'email': user.email,
            'role': user.role
        }, status=status.HTTP_200_OK)

