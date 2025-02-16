from django.db import models

class ContactSubmission(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    company_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    referral_source = models.CharField(max_length=255, blank=True, null=True)
    commands = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.email}"


class Testimonial(models.Model):
    name = models.CharField(max_length=255)
    message = models.TextField()
    user_image = models.ImageField(upload_to='testimonials/user_images/', blank=True, null=True)
    rating = models.IntegerField(default=0)  # Stores 1-5 rating
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name



