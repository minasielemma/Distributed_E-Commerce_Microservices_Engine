from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/orders/schema/', SpectacularAPIView.as_view(), name='openapi-schema'),
    path('api/orders/docs/', SpectacularSwaggerView.as_view(url_name='openapi-schema'), name='swagger-ui'),
    path('api/orders/', include('orders.urls')),
    path('swagger/', SpectacularSwaggerView.as_view(url_name='openapi-schema'), name='schema-swagger-ui'),
]
