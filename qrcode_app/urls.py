from django.urls import path
from . import views

urlpatterns = [
    path('', views.scan_qr, name='scan_qr'),
    path('process/', views.process_qr, name='process_qr'),
    path('clear/', views.clear_canteen_session, name='clear_canteen_session'),
    path('choose/', views.choose_canteen, name='choose_canteen'),
    path('vendor/qr/', views.vendor_qr, name='vendor_qr'),
    path('vendor/qr/download/', views.download_qr, name='download_qr'),
]
