"""Sprint-1 question management and submission flows (issues #12, #16, #17)."""

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import QuestionForm
from .models import Answer, Attempt, Exam, Question


def _staff_only(request):
    return request.user.is_staff


@login_required
def question_list(request, exam_id):
    if not _staff_only(request):
        return HttpResponseForbidden('Only staff members may manage questions.')
    exam = get_object_or_404(Exam, pk=exam_id)
    return render(request, 'exams/questions.html', {
        'exam': exam,
        'questions': exam.questions.all(),
    })


@login_required
def question_create(request, exam_id):
    if not _staff_only(request):
        return HttpResponseForbidden('Only staff members may manage questions.')
    exam = get_object_or_404(Exam, pk=exam_id)
    form = QuestionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        question = form.save(commit=False)
        question.exam = exam
        question.save()
        return redirect('exams:questions', exam_id=exam.pk)
    return render(request, 'exams/question_form.html', {'exam': exam, 'form': form, 'editing': False})


@login_required
def question_edit(request, exam_id, question_id):
    if not _staff_only(request):
        return HttpResponseForbidden('Only staff members may manage questions.')
    exam = get_object_or_404(Exam, pk=exam_id)
    question = get_object_or_404(Question, pk=question_id, exam=exam)
    form = QuestionForm(request.POST or None, instance=question)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('exams:questions', exam_id=exam.pk)
    return render(request, 'exams/question_form.html', {'exam': exam, 'form': form, 'editing': True})


@login_required
def question_delete(request, exam_id, question_id):
    if not _staff_only(request):
        return HttpResponseForbidden('Only staff members may manage questions.')
    exam = get_object_or_404(Exam, pk=exam_id)
    question = get_object_or_404(Question, pk=question_id, exam=exam)
    if request.method == 'POST':
        question.delete()
        return redirect('exams:questions', exam_id=exam.pk)
    return render(request, 'exams/question_delete.html', {'exam': exam, 'question': question})


def _question_number(value, total, default=1):
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return max(1, min(number, total)) if total else 1


@login_required
def take_exam(request, exam_id):
    """Persistent answers and review flags, while preserving original navigation and JSON API."""
    exam = get_object_or_404(Exam, pk=exam_id)
    attempt = Attempt.objects.filter(exam=exam, student=request.user).first()
    if attempt and attempt.status == Attempt.SUBMITTED:
        if request.method != 'GET':
            return HttpResponse('This attempt has already been submitted.', status=409)
        return render(request, 'exams/submitted.html', {'exam': exam, 'attempt': attempt})

    now = timezone.now()
    if exam.is_upcoming(now):
        msg = f'This exam has not started yet. Early access is blocked on server. Scheduled start: {exam.start_at:%Y-%m-%d %H:%M %Z}.'
        if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
            return JsonResponse({'error': msg, 'status': 'upcoming'}, status=403)
        return HttpResponseForbidden(msg)
    if exam.is_expired(now):
        msg = f'This exam availability window has expired. Access is blocked on server. Scheduled end: {exam.end_at:%Y-%m-%d %H:%M %Z}.'
        if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
            return JsonResponse({'error': msg, 'status': 'expired'}, status=403)
        return HttpResponseForbidden(msg)

    if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
        return JsonResponse({
            'id': exam.id, 'title': exam.title,
            'duration_minutes': exam.duration_minutes,
            'start_at': exam.start_at.isoformat(),
            'end_at': exam.end_at.isoformat(), 'status': 'available',
        })

    if request.method not in ('GET', 'POST'):
        return HttpResponse(status=405)

    # One attempt per student per exam. Navigating reloads persisted answers, not session state.
    attempt, _ = Attempt.objects.get_or_create(exam=exam, student=request.user)
    questions = list(exam.questions.all())
    total = len(questions)
    if request.method == 'POST' and total:
        current = _question_number(request.POST.get('current'), total)
        selected = request.POST.get('answer')
        review = request.POST.get('mark_for_review') == 'on'
        question = questions[current - 1]
        if selected in ('A', 'B', 'C', 'D'):
            answer, _ = Answer.objects.get_or_create(attempt=attempt, question=question)
            answer.selected_option = selected
            answer.marked_for_review = review
            answer.save()
            # Preserve legacy session behavior for teammates' Sprint-1 navigation tests.
            all_answers = request.session.get('exam_answers', {})
            answers = all_answers.get(str(exam.pk), {})
            answers[str(question.pk)] = selected
            all_answers[str(exam.pk)] = answers
            request.session['exam_answers'] = all_answers
        elif selected is None:
            # A review flag can be changed on an already-saved answer.
            existing = Answer.objects.filter(attempt=attempt, question=question).first()
            if existing is not None:
                existing.marked_for_review = review
                existing.save()
        # Invalid option values are ignored rather than stored.
        if request.POST.get('action') == 'review_submission':
            return redirect('exams:submit', exam_id=exam.pk)
        target = _question_number(request.POST.get('goto'), total, default=current)
        return redirect(f'{request.path}?question={target}')

    saved = {a.question_id: a for a in attempt.answers.all()}
    number = _question_number(request.GET.get('question'), total)
    question = questions[number - 1] if total else None
    selected_answer = saved.get(question.pk) if question else None
    navigator = [
        {'number': i, 'answered': bool(saved.get(q.pk) and saved[q.pk].selected_option),
         'current': i == number}
        for i, q in enumerate(questions, start=1)
    ]
    return render(request, 'exams/take_exam.html', {
        'exam': exam, 'current_time': now, 'user': request.user, 'attempt': attempt,
        'question': question, 'number': number, 'total': total,
        'selected': selected_answer.selected_option if selected_answer else None,
        'marked_for_review': selected_answer.marked_for_review if selected_answer else False,
        'navigator': navigator,
        'prev_number': number - 1 if number > 1 else None,
        'next_number': number + 1 if number < total else None,
    })


@login_required
def submit_exam(request, exam_id):
    exam = get_object_or_404(Exam, pk=exam_id)
    attempt = Attempt.objects.filter(exam=exam, student=request.user).first()
    if attempt and attempt.status == Attempt.SUBMITTED:
        if request.method == 'POST':
            return HttpResponse('This attempt has already been submitted.', status=409)
        return render(request, 'exams/submitted.html', {'exam': exam, 'attempt': attempt})

    now = timezone.now()
    if not exam.is_available(now):
        return HttpResponseForbidden('Exam submission is unavailable outside the exam window.')
    if not exam.questions.exists():
        return HttpResponse('Cannot submit an exam with no questions.', status=400)
    if request.method == 'GET':
        if attempt is None:
            attempt, _ = Attempt.objects.get_or_create(exam=exam, student=request.user)
        return render(request, 'exams/confirm_submission.html', {
            'exam': exam,
            'total': exam.questions.count(),
            'answered': attempt.answers.exclude(selected_option__isnull=True).count(),
        })
    if request.method != 'POST':
        return HttpResponse(status=405)
    if request.POST.get('confirmed') != 'yes':
        return HttpResponse('Confirmation is required.', status=400)

    with transaction.atomic():
        attempt, _ = Attempt.objects.get_or_create(exam=exam, student=request.user)
        attempt = Attempt.objects.select_for_update().get(pk=attempt.pk)
        if attempt.status == Attempt.SUBMITTED:
            return HttpResponse('This attempt has already been submitted.', status=409)
        # Score is authoritative on the server and is saved atomically with the lock.
        score = sum(
            1 for answer in attempt.answers.select_related('question')
            if answer.selected_option == answer.question.correct_option
            and answer.question.exam_id == exam.pk
        )
        attempt.score = score
        attempt.status = Attempt.SUBMITTED
        attempt.submitted_at = timezone.now()
        attempt.save(update_fields=['score', 'status', 'submitted_at'])
    return redirect('exams:take', exam_id=exam.pk)
