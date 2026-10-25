from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login

def home(request):
    """Home page - directs users to appropriate login based on role."""
    if request.user.is_authenticated:
        return redirect('accounts:admin_dashboard' if request.user.is_staff else 'accounts:student_dashboard')
    return render(request, 'core/home.html')


def admin_login_redirect(request):
    """Redirect to admin login."""
    return redirect('accounts:login')


def student_login_redirect(request):
    """Redirect to student login."""
    return redirect('accounts:student_login')