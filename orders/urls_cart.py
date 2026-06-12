from django.urls import path
from . import views

urlpatterns = [
    path('', views.cart_view, name='cart'),
    path('add/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('update/<int:item_id>/', views.update_cart_quantity, name='update_cart_qty'),
    path('checkout/', views.checkout, name='checkout'),
    path('mock-payment/', views.mock_payment, name='mock_payment'),
]
