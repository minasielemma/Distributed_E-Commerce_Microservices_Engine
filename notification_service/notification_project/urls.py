from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/notifications/schema/', SpectacularAPIView.as_view(), name='openapi-schema'),
    path('api/notifications/docs/', SpectacularSwaggerView.as_view(url_name='openapi-schema'), name='swagger-ui'),
    path('api/notifications/', include('notifications.urls')),
    path('api/auth/notifications/', include('notifications.urls')), # Backward compatibility route
    path('swagger/', SpectacularSwaggerView.as_view(url_name='openapi-schema'), name='schema-swagger-ui'),
]
