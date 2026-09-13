from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView,
    CustomTokenObtainPairView,
    CreateTenantView,
    TenantListView,
    AdminConfigureSubscriptionView,
    UserProfileView,
    ActivityLogListView,
    CreateInternalActivityLogView,
    UserAddressViewSet,
    NotificationViewSet,
    UserLookupView
)

router = DefaultRouter()
router.register(r'addresses', UserAddressViewSet, basename='address')
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('tenant/create/', CreateTenantView.as_view(), name='tenant_create'),
    path('tenant/list/', TenantListView.as_view(), name='tenant_list'),
    path('tenants/', TenantListView.as_view(), name='tenants_list'),
    path('admin/tenants/<uuid:pk>/configure-subscription/', AdminConfigureSubscriptionView.as_view(), name='admin_configure_subscription'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('users/lookup/', UserLookupView.as_view(), name='user_lookup'),
    path('activity/', ActivityLogListView.as_view(), name='user_activity'),
    path('activity/create-internal/', CreateInternalActivityLogView.as_view(), name='activity_create_internal'),
    path('audit-logs/create-internal/', CreateInternalActivityLogView.as_view(), name='audit_create_internal'),
    path('', include(router.urls)),
]
