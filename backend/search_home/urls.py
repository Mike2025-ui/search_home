from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('verify-code/', views.verify_code, name='verify_code'),
]