from django import forms
from .models import ContactSubmission, Testimonial

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactSubmission
        fields = [
            "first_name",
            "last_name",
            "email",
            "company_name",
            "phone_number",
            "referral_source",
            "commands",
        ]

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if ContactSubmission.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email
    
class TestimonialForm(forms.ModelForm):
    message = forms.CharField(
        max_length=133,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': "Write your review here..."}),
        error_messages={'max_length': "Message cannot exceed 133 characters."}
    )
    class Meta:
        model = Testimonial
        fields = ['name', 'message', 'rating', 'user_image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control mt-3', 'placeholder': 'Full Name'}),
            'user_image': forms.FileInput(attrs={'class': 'form-control mt-3'}),
            'rating': forms.HiddenInput(),
        }

    def clean_message(self):
        message = self.cleaned_data.get("message")
        if len(message) > 200:  # Set the limit (adjust as needed)
            raise forms.ValidationError("Message cannot exceed 133 characters.")
        return message