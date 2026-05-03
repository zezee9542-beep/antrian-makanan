from django.urls import path
from . import views

urlpatterns = [
    path('<int:canteen_id>/', views.menu_list, name='menu_list'),
    path('item/<int:item_id>/', views.menu_detail, name='menu_detail'),
]
