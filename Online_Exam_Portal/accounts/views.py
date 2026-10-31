from django.contrib.auth import authenticate, get_user_model, login
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.views.decorators.http import require_POST
from exams.models import Attempt, Exam


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
def admin_submissions(request):
    """Show the student roster and attempt status for a staff-selected exam."""
    if not request.user.is_staff:
        return HttpResponseForbidden("You don't have access to exam submissions.")

    exams = Exam.objects.all()
    selected_exam = None
    roster = []
    exam_id = request.GET.get('exam')
    if exam_id:
        selected_exam = exams.filter(pk=exam_id).first()
        if selected_exam is not None:
            attempts = {
                attempt.student_id: attempt
                for attempt in Attempt.objects.filter(exam=selected_exam).select_related('student')
            }
            total_questions = selected_exam.questions.count()
            students = get_user_model().objects.filter(
                is_staff=False,
                is_active=True,
            ).order_by('username')
            for student in students:
                attempt = attempts.get(student.pk)
                submitted = attempt is not None and attempt.status == Attempt.SUBMITTED
                roster.append({
                    'student': student,
                    'attempt': attempt,
                    'state': 'Submitted' if submitted else ('In progress' if attempt else 'Not started'),
                    'score': f'{attempt.score} / {total_questions}' if submitted and attempt.score is not None else '—',
                })

    return render(request, 'accounts/admin_submissions.html', {
        'user': request.user,
        'is_admin': True,
        'exams': exams,
        'selected_exam': selected_exam,
        'roster': roster,
        'current_time': timezone.now(),
    })


@login_required
@require_POST
def release_exam_results(request, exam_id):
    """Release submitted scores once the exam window is closed and attempts are complete."""
    if not request.user.is_staff:
        return HttpResponseForbidden("You don't have access to release exam results.")
    exam = get_object_or_404(Exam, pk=exam_id)
    if exam.end_at > timezone.now() or exam.attempts.filter(status=Attempt.IN_PROGRESS).exists():
        messages.error(request, 'Results can be released after the exam closes and all attempts are submitted.')
    elif not exam.results_released:
        exam.results_released = True
        exam.save(update_fields=['results_released'])
        messages.success(request, f'Results released for {exam.title}.')
    else:
        messages.info(request, f'Results are already released for {exam.title}.')
    return redirect(f"{reverse('accounts:admin_submissions')}?exam={exam.pk}")


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
