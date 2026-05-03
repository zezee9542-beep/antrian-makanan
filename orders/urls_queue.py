from django.urls import path
from . import views

urlpatterns = [
    path('<int:order_id>/', views.queue_status, name='queue_status'),
    path('<int:order_id>/api/', views.queue_status_api, name='queue_status_api'),
]
