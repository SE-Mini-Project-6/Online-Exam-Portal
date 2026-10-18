from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden


def admin_login(request):
    """
    Admin login view with secure password handling.

    - Uses Django's built-in authenticate() which validates
      salted password hashes
    - On success, logs in and redirects based on user role
    - On failure, re-renders login form with error message
    """
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

    return render(request, 'accounts/login.html')


def student_login(request):
    """
    Student login view with secure password handling.

    - Shares authentication logic with admin_login
    - Role-based redirection after successful login
    """
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

    return render(request, 'accounts/login.html')


@login_required
def admin_dashboard(request):
    """Admin dashboard - only accessible to staff users."""
    if not request.user.is_staff:
        return HttpResponseForbidden("You don't have access to the admin dashboard.")

    # Admin-specific context
    return render(request, 'accounts/admin_dashboard.html', {
        'user': request.user,
        'is_admin': True,
    })


@login_required
def student_dashboard(request):
    """Student dashboard - accessible to all authenticated students."""
    # Student-specific context
    return render(request, 'accounts/student_dashboard.html', {
        'user': request.user,
        'is_admin': False,
    })


def logout_view(request):
    """Logout view that clears the session."""
    from django.contrib.auth import logout
    logout(request)
    messages.info(request, 'You have been successfully logged out.')
    return redirect('accounts:login')