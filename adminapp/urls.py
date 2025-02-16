from django.urls import path
from . import views

urlpatterns = [

    # admin login, logout
    path('login/admin/', views.admin_login, name='admin_login'),
    path('logout/admin/', views.admin_logout, name='admin_logout'),

    # admin dashboard
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),

    # all enquiry
    path('all_enquiry/admin/', views.all_enquiry, name='all_enquiry'),

    # testimonials
    path('testimonials/', views.testimonial_list, name='testimonial_list'),
    path('testimonials/add/', views.add_or_edit_testimonial, name='add_testimonial'),
    path('testimonials/edit/<int:testimonial_id>/', views.add_or_edit_testimonial, name='edit_testimonial'),
    path('testimonials/delete/<int:id>/', views.delete_testimonial, name='delete_testimonial'),


    path('submit-contact/', views.submit_contact, name='submit_contact'),
]
