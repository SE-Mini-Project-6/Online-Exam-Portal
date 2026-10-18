from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login

def home(request):
    """Home page - directs users to appropriate login based on role."""
    return render(request, 'core/home.html')


def admin_login_redirect(request):
    """Redirect to admin login."""
    return redirect('accounts:login')


def student_login_redirect(request):
    """Redirect to student login."""
    return redirect('accounts:student_login')