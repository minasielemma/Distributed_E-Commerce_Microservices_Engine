from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/notifications/', include('notifications.urls')),
    path('api/auth/notifications/', include('notifications.urls')), # Backward compatibility route
]
