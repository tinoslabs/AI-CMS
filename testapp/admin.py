from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    list_display = ('id', 'email', 'username', 'role', 'phone_number', 'qr_verified', 'qr_delivered', 'is_active')  # Display role and phone_number
    list_filter = ('role', 'is_active', 'qr_verified', 'qr_delivered')  # Add filters for easy management
    search_fields = ('email', 'username', 'phone_number')  # Allow searching by email, username, or phone number
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal Info', {'fields': ('phone_number', 'user_image')}),
        ('QR Code Info', {'fields': ('qr_code', 'qr_code_data', 'qr_delivered', 'qr_verified')}),
        ('Role Information', {'fields': ('role',)}),  # Ensure role is editable
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
 
     
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'role', 'phone_number', 'is_active', 'qr_delivered', 'qr_verified'),
        }),
    )

admin.site.register(User, CustomUserAdmin)

# admin.site.register(User)
