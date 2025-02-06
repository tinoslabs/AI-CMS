# models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.core.files.base import ContentFile
import os
from hashlib import sha256

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('volunteer', 'Volunteer'),
    )

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='volunteer')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.username} ({self.role})"

    class Meta:
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
        ]

def participant_image_upload_path(instance, filename):
    """Store participant images in a dedicated folder with the same filename."""
    return f"participant_images/{filename}"

class Participant(models.Model):
    username = models.CharField(max_length=150)  # Allow duplicates
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, unique=True)
    designation = models.CharField(max_length=255)
    
    user_image = models.ImageField(
        upload_to=participant_image_upload_path,
        default='default/default_profile.jpg'
    )

    qr_code = models.ImageField(upload_to="qr_codes/%Y/%m/")
    qr_code_data = models.CharField(max_length=255, unique=True)
    qr_delivered = models.BooleanField(default=False)
    qr_verified = models.BooleanField(default=False)

    # Relations to User model
    registered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='registered_participants'
    )
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='verified_participants'
    )

    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # def save(self, *args, **kwargs):
    #     """Ensure the image filename is preserved when saving."""
    #     if self.user_image and hasattr(self.user_image, 'name'):
    #         self.user_image.name = os.path.basename(self.user_image.name)  # Keep the original filename
        
    #     super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} - {self.email}"

    class Meta:
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['qr_code_data']),
            models.Index(fields=['created_at']),
        ]
