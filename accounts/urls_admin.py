from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('api/dashboard/', views.admin_dashboard_api, name='admin_dashboard_api'),
    path('api/users/', views.admin_users_api, name='admin_users_api'),
    path('api/monitoring/', views.admin_monitoring_api, name='admin_monitoring_api'),
    path('users/', views.admin_users, name='admin_users'),
    path('users/<int:user_id>/profile/', views.admin_user_profile, name='admin_user_profile'),
    path('users/<int:user_id>/toggle/', views.admin_toggle_user, name='admin_toggle_user'),
    path('canteens/', views.admin_canteens, name='admin_canteens'),
    path('canteens/<int:canteen_id>/', views.admin_canteen_detail, name='admin_canteen_detail'),
    path('canteens/<int:canteen_id>/add-menu/', views.admin_add_menu, name='admin_add_menu'),
    path('monitoring/', views.admin_monitoring, name='admin_monitoring'),
    path('logs/', views.admin_logs, name='admin_logs'),
]
