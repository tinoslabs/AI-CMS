from django.contrib.auth.models import AbstractUser
from django.db import models
import os
from hashlib import sha256
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage


def user_image_upload_path(instance, filename):
    """Store images without renaming them in backend."""
    return f"user_images/{filename}"

class User(AbstractUser):
    ROLE_CHOICES = (
        ('participant', 'Participant'),
        ('volunteer', 'Volunteer'),
    )

    username = models.CharField(max_length=150, unique=False)  # Allow duplicate usernames
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, unique=True, blank=True, null=True)

    user_image = models.ImageField(
        upload_to=user_image_upload_path,
        default='default/default_profile.jpg',
        blank=True, 
        null=True
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='participant')

    qr_code = models.ImageField(upload_to="qr_codes/%Y/%m/", blank=True, null=True)
    qr_code_data = models.CharField(max_length=255, unique=True, null=True, blank=True)
    qr_delivered = models.BooleanField(default=False)
    qr_verified = models.BooleanField(default=False)

    fingerprint_template = models.BinaryField(null=True, blank=True)  # Store raw fingerprint template
    fingerprint_template_hash = models.CharField(max_length=64, blank=True, null=True)  # Store hashed version
    fingerprint_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # verified by
    verified_by = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='verified_participants',
        limit_choices_to={'role': 'volunteer'}  # Ensure only volunteers can verify
    )
    verified_at = models.DateTimeField(null=True, blank=True)  # Timestamp of verification


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.username} ({self.role})"
    
    
    def verify_participant(self, volunteer):
        """
        Method to record QR code verification by a volunteer
        """
        from django.utils import timezone
        
        if volunteer.role != 'volunteer':
            raise ValueError("Only volunteers can verify participants")
        
        self.verified_by = volunteer
        self.verified_at = timezone.now()
        self.qr_verified = True
        self.save()

    def save(self, *args, **kwargs):
        """Hash fingerprint template before saving."""
        if self.fingerprint_template:
            self.fingerprint_template_hash = sha256(self.fingerprint_template).hexdigest()
        super().save(*args, **kwargs)

    class Meta:
        indexes = [
            models.Index(fields=['fingerprint_template_hash']),  # Indexing for fast lookups
        ]


