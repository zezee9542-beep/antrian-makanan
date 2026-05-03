from django.urls import path
from . import views

urlpatterns = [
    path('', views.notifications_list, name='notifications'),
    path('api/', views.notifications_api, name='notifications_api'),
    path('<int:notif_id>/read/', views.mark_read, name='mark_read'),
]
