from django.contrib.auth.models import AbstractUser
from django.db import models
import os

def user_image_upload_path(instance, filename):
    """Generate a file path for new user image uploads."""
    ext = filename.split('.')[-1]  # Get the file extension
    filename = f"{instance.id}_{instance.username}.{ext}"  # Format: "id_username.jpg"
    return os.path.join("student_images", filename)  # Save inside "student_images/"


from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('participant', 'Participant'),
        ('volunteer', 'Volunteer'),
    )

    username = models.CharField(max_length=150, unique=False)  # Remove uniqueness
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, unique=True, blank=True, null=True)
    user_image = models.ImageField(upload_to=user_image_upload_path, default='default/default_profile.jpg', blank=True, null=True)
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='participant')
    
    qr_code = models.ImageField(upload_to="qr_codes/%Y/%m/", blank=True, null=True)
    qr_code_data = models.CharField(max_length=255, unique=True, null=True, blank=True)
    qr_delivered = models.BooleanField(default=False)
    qr_verified = models.BooleanField(default=False)

    fingerprint_data = models.TextField(null=True, blank=True)  # Store Base64 fingerprint
    fingerprint_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.username} ({self.role})"
