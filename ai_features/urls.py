from django.urls import path
from . import views

urlpatterns = [
    path('ai/recommend/', views.ai_recommend, name='ai_recommend'),
    path('ai/predict/', views.ai_predict, name='ai_predict'),
    path('ai/anomaly/', views.ai_anomaly_check, name='ai_anomaly'),
]
