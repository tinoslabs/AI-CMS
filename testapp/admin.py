# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User, Participant

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_active', 'date_joined', 'last_login')
    list_filter = ('role', 'is_active', 'date_joined', 'last_login')
    search_fields = ('username', 'email')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'is_active', 'is_staff'),
        }),
    )

@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'phone_number', 'designation', 
                   'qr_verified', 'verified_by_display', 'verified_at', 
                   'registered_by_display', 'created_at')
    
    list_filter = ('qr_verified', 'verified_at', 'created_at', 'designation')
    search_fields = ('username', 'email', 'phone_number')
    readonly_fields = ('qr_code_data', 'created_at', 'updated_at')
    ordering = ('-created_at',)

    def verified_by_display(self, obj):
        if obj.verified_by:
            return f"{obj.verified_by.username} ({obj.verified_by.email})"
        return "-"
    verified_by_display.short_description = 'Verified By'

    def registered_by_display(self, obj):
        if obj.registered_by:
            return f"{obj.registered_by.username} ({obj.registered_by.email})"
        return "-"
    registered_by_display.short_description = 'Registered By'

    fieldsets = (
        ('Basic Information', {
            'fields': ('username', 'email', 'phone_number', 'designation', 'user_image')
        }),
        ('QR Code Information', {
            'fields': ('qr_code', 'qr_code_data', 'qr_verified')
        }),
        ('Verification Details', {
            'fields': ('verified_by', 'verified_at')
        }),
        ('Registration Details', {
            'fields': ('registered_by', 'created_at', 'updated_at')
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # If this is a new participant
            obj.registered_by = request.user
        super().save_model(request, obj, form, change)