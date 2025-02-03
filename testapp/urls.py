from django.urls import path
from .import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # reg students
    path('register/', views.register_user, name='register_user'), 
    path('verify_qr_code/', views.verify_qr_code, name='verify_qr_code'),
    path('verify_fingerprint/', views.verify_fingerprint, name='verify_fingerprint'),

]
