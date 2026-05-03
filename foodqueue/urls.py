from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('auth/', include('accounts.urls_auth')),
    path('dashboard/', include('accounts.urls_dashboard')),
    path('menu/', include('menu.urls')),
    path('orders/', include('orders.urls')),
    path('cart/', include('orders.urls_cart')),
    path('queue/', include('orders.urls_queue')),
    path('vendor/', include('menu.urls_vendor')),
    path('admin-panel/', include('accounts.urls_admin')),
    path('scan/', include('qrcode_app.urls')),
    path('api/', include('ai_features.urls')),
    path('notifications/', include('notifications.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
