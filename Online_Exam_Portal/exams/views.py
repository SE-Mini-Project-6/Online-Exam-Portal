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


@login_required
def take_exam(request, exam_id):
    """
    Student exam access view with strict server-side window enforcement.
    Blocks early access (before start_at) and expired access (after end_at) with HTTP 403.
    """
    exam = get_object_or_404(Exam, pk=exam_id)
    now = timezone.now()

    # Server-side Window Enforcement
    if exam.is_upcoming(now):
        msg = (
            f"This exam has not started yet. Early access is blocked on server. "
            f"Scheduled start: {exam.start_at.strftime('%Y-%m-%d %H:%M %Z')}."
        )
        if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
            return JsonResponse({'error': msg, 'status': 'upcoming'}, status=403)
        return HttpResponseForbidden(msg)

    if exam.is_expired(now):
        msg = (
            f"This exam availability window has expired. Access is blocked on server. "
            f"Scheduled end: {exam.end_at.strftime('%Y-%m-%d %H:%M %Z')}."
        )
        if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
            return JsonResponse({'error': msg, 'status': 'expired'}, status=403)
        return HttpResponseForbidden(msg)

    # In active window: Grant access
    if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
        return JsonResponse({
            'id': exam.id,
            'title': exam.title,
            'duration_minutes': exam.duration_minutes,
            'start_at': exam.start_at.isoformat(),
            'end_at': exam.end_at.isoformat(),
            'status': 'available',
        })

    questions = list(exam.questions.all())
    total = len(questions)

    # Answers are kept in the session only (Sprint 1 design deviation, see docs).
    all_answers = request.session.get('exam_answers', {})
    answers = all_answers.get(str(exam.id), {})

    if request.method == 'POST' and total:
        current = _question_number(request.POST.get('current'), total)
        selected = request.POST.get('answer')
        if selected in dict(Question.OPTION_CHOICES):
            answers[str(questions[current - 1].id)] = selected
            all_answers[str(exam.id)] = answers
            request.session['exam_answers'] = all_answers
        target = _question_number(request.POST.get('goto'), total, default=current)
        return redirect(f"{request.path}?question={target}")

    number = _question_number(request.GET.get('question'), total)
    question = questions[number - 1] if total else None

    navigator = [
        {'number': i, 'answered': str(q.id) in answers, 'current': i == number}
        for i, q in enumerate(questions, start=1)
    ]

    return render(request, 'exams/take_exam.html', {
        'exam': exam,
        'current_time': now,
        'user': request.user,
        'question': question,
        'number': number,
        'total': total,
        'selected': answers.get(str(question.id)) if question else None,
        'navigator': navigator,
        'prev_number': number - 1 if number > 1 else None,
        'next_number': number + 1 if number < total else None,
    })


def _question_number(value, total, default=1):
    """Parse a 1-based question number, clamped to the valid range."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return max(1, min(number, total)) if total else 1

