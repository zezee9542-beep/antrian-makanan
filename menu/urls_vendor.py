from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.vendor_dashboard, name='vendor_dashboard'),
    path('menu/', views.vendor_menu, name='vendor_menu'),
    path('menu/add/', views.vendor_menu_add, name='vendor_menu_add'),
    path('menu/<int:item_id>/edit/', views.vendor_menu_edit, name='vendor_menu_edit'),
    path('menu/<int:item_id>/delete/', views.vendor_menu_delete, name='vendor_menu_delete'),
    path('menu/<int:item_id>/toggle/', views.vendor_toggle_item, name='vendor_toggle_item'),
    path('orders/', views.vendor_orders, name='vendor_orders'),
    path('orders/<int:order_id>/', views.vendor_order_detail, name='vendor_order_detail'),
    path('orders/<int:order_id>/update/', views.vendor_update_order_status, name='vendor_update_order'),
    path('stats/', views.vendor_stats, name='vendor_stats'),
]
