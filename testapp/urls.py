from django.urls import path
from .import views

urlpatterns = [
    path('register/', views.register_user, name='register_user'),
    path('verify_qr_code/', views.verify_qr_code, name='verify_qr_code'),

]
