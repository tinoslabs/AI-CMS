from django.contrib import admin
from django.utils.html import format_html
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'delivered', 'verified')

    def qr_code_preview(self, obj):
        if obj.qr_code:
            return format_html('<img src="{}" width="50" height="50" />', obj.qr_code.url)
        return "No QR Code"

    qr_code_preview.short_description = "QR Code"
