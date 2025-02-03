# from django.contrib.auth.models import AbstractUser
# from django.db import models
# import os
# from hashlib import sha256


# def user_image_upload_path(instance, filename):
#     """Generate a file path for new user image uploads."""
#     ext = filename.split('.')[-1]  # Get the file extension
#     filename = f"{instance.id}_{instance.username}.{ext}"  # Format: "id_username.jpg"
#     return os.path.join("student_images", filename)  # Save inside "student_images/"


# from django.contrib.auth.models import AbstractUser
# from django.db import models

# class User(AbstractUser):
#     ROLE_CHOICES = (
#         ('participant', 'Participant'),
#         ('volunteer', 'Volunteer'),
#     )

#     username = models.CharField(max_length=150, unique=False)  # Remove uniqueness
#     email = models.EmailField(unique=True)
#     phone_number = models.CharField(max_length=15, unique=True, blank=True, null=True)
#     user_image = models.ImageField(upload_to=user_image_upload_path, default='default/default_profile.jpg', blank=True, null=True)
    
#     role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='participant')
    
#     qr_code = models.ImageField(upload_to="qr_codes/%Y/%m/", blank=True, null=True)
#     qr_code_data = models.CharField(max_length=255, unique=True, null=True, blank=True)
#     qr_delivered = models.BooleanField(default=False)
#     qr_verified = models.BooleanField(default=False)

#     fingerprint_template = models.BinaryField(null=True, blank=True)  # Store raw fingerprint template
#     fingerprint_template_hash = models.CharField(max_length=64, blank=True, null=True)  # Store hashed version
#     fingerprint_verified = models.BooleanField(default=False)

#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     USERNAME_FIELD = 'email'
#     REQUIRED_FIELDS = ['username']

#     def __str__(self):
#         return f"{self.username} ({self.role})"

#     def save(self, *args, **kwargs):
#         """
#         Automatically hashes the fingerprint before saving it in the database.
#         Ensures that we store only the hashed version for fast comparisons.
#         """
#         if self.fingerprint_template:
#             self.fingerprint_template_hash = sha256(self.fingerprint_template).hexdigest()
#         super().save(*args, **kwargs)

#     class Meta:
#         indexes = [
#             models.Index(fields=['fingerprint_template_hash']),  # Indexing for fast lookups
#         ]

    

from django.contrib.auth.models import AbstractUser
from django.db import models
import os
from hashlib import sha256
from django.db.models.signals import pre_save
from django.dispatch import receiver

def user_image_upload_path(instance, filename):
    """Temporary path before instance is saved."""
    ext = filename.split('.')[-1]  # Extract file extension
    return os.path.join("student_images", f"temp_{filename}")  # Temporary filename

class User(AbstractUser):
    ROLE_CHOICES = (
        ('participant', 'Participant'),
        ('volunteer', 'Volunteer'),
    )

    username = models.CharField(max_length=150, unique=False)  # Allow duplicate usernames
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, unique=True, blank=True, null=True)
    user_image = models.ImageField(upload_to=user_image_upload_path, default='default/default_profile.jpg', blank=True, null=True)
    
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

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.username} ({self.role})"

    def save(self, *args, **kwargs):
        """Hash fingerprint template before saving."""
        if self.fingerprint_template:
            self.fingerprint_template_hash = sha256(self.fingerprint_template).hexdigest()
        super().save(*args, **kwargs)

    class Meta:
        indexes = [
            models.Index(fields=['fingerprint_template_hash']),  # Indexing for fast lookups
        ]


@receiver(pre_save, sender=User)
def rename_user_image(sender, instance, **kwargs):
    """Rename user_image to follow id_username format before saving."""
    if instance.pk and instance.user_image:
        ext = instance.user_image.name.split('.')[-1]  # Extract file extension
        new_filename = f"{instance.pk}_{instance.username}.{ext}"  # Format: "id_username.jpg"
        instance.user_image.name = os.path.join("student_images", new_filename)

