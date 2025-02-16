from django.urls import path
from .import views

urlpatterns = [
    path('', views.index, name='index'),

    path('api/login/', views.login_view, name='login'),
    path('api/logout/', views.logout_view, name='logout'),

    path('api/register/', views.register_participant, name='register'),
    path('api/verify_qr_code/', views.verify_participant, name='verify_qr_code'),

    path('api/verify_face/', views.verify_face_api, name='verify_face_api'),
    path('verify_face/', views.verify_face, name='verify_face'),
    
    path('export/', views.export_participants_to_excel, name='export'),
    path('download/', views.download_all_images, name='download'),


]


