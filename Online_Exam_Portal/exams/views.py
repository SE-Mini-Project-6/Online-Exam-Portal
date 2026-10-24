from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import ExamForm
from .models import Exam, Question


@login_required
def create_exam(request):
    """Admin-only view to configure a new exam with duration and availability window."""
    if not request.user.is_staff:
        return HttpResponseForbidden("You don't have access to exam configuration.")

    if request.method == 'POST':
        form = ExamForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('accounts:admin_dashboard')
    else:
        form = ExamForm()

    return render(request, 'exams/create_exam.html', {'form': form})


@login_required
def available_exams(request):
    """
    List configured exams for students with scheduled times and availability status.
    Accessible to all authenticated users.
    """
    exams = Exam.objects.all().order_by('start_at')
    now = timezone.now()

    if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
        data = [
            {
                'id': exam.id,
                'title': exam.title,
                'duration_minutes': exam.duration_minutes,
                'start_at': exam.start_at.isoformat(),
                'end_at': exam.end_at.isoformat(),
                'status': exam.get_status(now),
                'status_label': exam.get_status_label(now),
                'is_available': exam.is_available(now),
            }
            for exam in exams
        ]
        return JsonResponse({'exams': data})

    return render(request, 'exams/available_exams.html', {
        'exams': exams,
        'current_time': now,
        'user': request.user,
    })

from .sprint1_views import take_exam  # noqa: E402; shared URL handler
