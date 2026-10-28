from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
from django.utils import timezone
from exams.models import Exam


def landing_url_name(user):
    """Name of the landing page for a signed-in user's role."""
    return 'accounts:admin_dashboard' if user.is_staff else 'accounts:student_dashboard'


def admin_login(request):
    """
    Admin login view with secure password handling.

    - Uses Django's built-in authenticate() which validates
      salted password hashes
    - On success, logs in and redirects based on user role
    - On failure, re-renders login form with error message
    """
    if request.method == 'GET' and request.user.is_authenticated:
        return redirect(landing_url_name(request.user))

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Django's authenticate handles password verification
        # with salted password hashing (PBKDF2 with HMAC)
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Check role - is_staff indicates admin privileges
            login(request, user)

            # Role-aware session redirect
            if user.is_staff:
                messages.success(request, f'Welcome, {user.username}!')
                return redirect('accounts:admin_dashboard')
            else:
                messages.success(request, f'Welcome, {user.username}!')
                return redirect('accounts:student_dashboard')
        else:
            # Invalid credentials rejected - generic error to avoid username enumeration
            messages.error(request, 'Invalid username or password.')

    return render(request, 'accounts/login.html', {'role': 'admin'})


def student_login(request):
    """
    Student login view with secure password handling.

    - Shares authentication logic with admin_login
    - Role-based redirection after successful login
    """
    if request.method == 'GET' and request.user.is_authenticated:
        return redirect(landing_url_name(request.user))

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # Role-aware session redirect
            if user.is_staff:
                messages.info(request, 'Admin privileges detected. Redirecting to admin portal.')
                return redirect('accounts:admin_dashboard')
            else:
                messages.success(request, f'Welcome, Student {user.username}!')
                return redirect('accounts:student_dashboard')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'accounts/login.html', {'role': 'student'})


@login_required
def admin_dashboard(request):
    """Admin dashboard - only accessible to staff users."""
    if not request.user.is_staff:
        return HttpResponseForbidden("You don't have access to the admin dashboard.")

    # Admin-specific context
    return render(request, 'accounts/admin_dashboard.html', {
        'user': request.user,
        'is_admin': True,
        'exams': Exam.objects.all(),
    })


@login_required
def student_dashboard(request):

    """Student dashboard - accessible to all authenticated students."""
    if request.user.is_staff:
        return redirect('accounts:admin_dashboard')
    exams = Exam.objects.all().order_by('start_at')
    now = timezone.now()
    return render(request, 'accounts/student_dashboard.html', {
        'user': request.user,
        'is_admin': False,
        'exams': exams,
        'current_time': now,
    })



@require_POST
def logout_view(request):
    """
    Logout view that clears the session.

    POST-only and CSRF-protected (no csrf_exempt): a GET or cross-site request must not
    be able to sign a user out (SEC-REQ-01/02). The navbar logout control is a POST form.
    """
    from django.contrib.auth import logout
    logout(request)
    messages.info(request, 'You have been successfully logged out.')
    return redirect('accounts:login')