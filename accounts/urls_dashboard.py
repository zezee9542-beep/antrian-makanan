from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard_redirect'),
    path('menu/', views.student_menu_view, name='student_menu'),
    path('menu/<int:item_id>/', views.student_menu_detail_view, name='student_menu_detail'),
]
