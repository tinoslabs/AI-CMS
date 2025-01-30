# models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinLengthValidator

class User(AbstractUser):
    username = models.CharField(max_length=150, unique=False) 
    email = models.EmailField(unique=True)  # Ensure email remains unique
    phone_number = models.CharField(max_length=15, unique=True, blank=True, null=True)  # Add phone number
    user_image = models.ImageField(upload_to="student_images/%Y/%m/", default='default/default_profile.jpg', blank=True, null=True)
    qr_code = models.ImageField(
        upload_to="qr_codes/%Y/%m/",
        blank=True,
        null=True
    )
    qr_code_data = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True
    )
    delivered = models.BooleanField(default=False)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'  # Use email as the primary identifier
    REQUIRED_FIELDS = ['username']  # Keep username, but it's not unique

    class Meta:
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['email']),
            models.Index(fields=['qr_code_data']),
        ]
        

    def __str__(self):
        return f"{self.username} ({self.email})"
