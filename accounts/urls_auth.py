from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('register/pending/', views.register_pending_view, name='register_pending'),
    path('logout/', views.logout_view, name='logout'),
]
