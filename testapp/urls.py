from django.urls import path
from .import views

urlpatterns = [
    path('', views.index, name='index'),

    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('register/', views.register_participant, name='register'),
    path('verify_qr_code/', views.verify_participant, name='verify_qr_code'),

]
