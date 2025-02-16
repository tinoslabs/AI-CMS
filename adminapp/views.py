from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .forms import ContactForm, TestimonialForm
from .models import ContactSubmission, Testimonial
from django.shortcuts import render, redirect,  get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test


def admin_login(request):
    return render(request, 'admin/admin_login.html')



def is_admin(user):
    return user.is_authenticated and user.is_superuser  # Restricts to superusers

def admin_login(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('admin_dashboard')  # Redirect if already logged in
    
    if request.method == "POST":
        email = request.POST.get("email-username")
        password = request.POST.get("password")
        user = authenticate(request, email=email, password=password)
        
        if user is not None and user.is_superuser:
            login(request, user)
            return redirect("admin_dashboard")  # Replace with your dashboard URL name
        else:
            messages.error(request, "Invalid credentials or unauthorized access")
    
    return render(request, 'admin/admin_login.html')

@user_passes_test(is_admin, login_url='admin_login')
def admin_dashboard(request):
    return render(request, "admin/admin_index.html")  # Admin-only dashboard

def admin_logout(request):
    logout(request)
    return redirect("admin_login")  # Redirect to login page after logout



@csrf_exempt  # Only for testing, remove in production
def submit_contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({
                'status': 'success',
                'message': 'Thank you! Your message has been sent successfully.'
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'An error occured.',
                'errors': form.errors
            })
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})

def all_enquiry(request):
    enquiries = ContactSubmission.objects.all()
    return render(request, 'admin/all_enquiry.html', {'enquiries':enquiries})


# # Testimonial
def testimonial_list(request):
    testimonials = Testimonial.objects.all()
    return render(request, 'admin/testimonials/testimonial_list.html', {'testimonials': testimonials})


def add_or_edit_testimonial(request, testimonial_id=None):
    if testimonial_id:
        testimonial = get_object_or_404(Testimonial, id=testimonial_id)
    else:
        testimonial = None

    if request.method == "POST":
        form = TestimonialForm(request.POST, request.FILES, instance=testimonial)
        if form.is_valid():
            form.save()
            messages.success(request, "Testimonial saved successfully!")
            return redirect("testimonial_list")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = TestimonialForm(instance=testimonial)

    return render(request, "admin/testimonials/testimonial_form.html", {"form": form})

def delete_testimonial(request, id):
    testimonial = get_object_or_404(Testimonial, id=id)
    testimonial.delete()
    return redirect('testimonial_list')

