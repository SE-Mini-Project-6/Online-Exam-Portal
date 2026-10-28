"""JSON API for answer autosave (FR-07, NFR-02): PATCH /api/v1/attempts/{id}/answers/{questionId}."""
import json
import time
import uuid

from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse

from .models import Answer, Attempt, Question
from .timing import sync_attempt

OPTIONS = ('A', 'B', 'C', 'D')


def _error(status, code, message):
    return JsonResponse(
        {'error': {'code': code, 'message': message, 'requestId': uuid.uuid4().hex}},
        status=status,
    )


def _parse_payload(request):
    """Return (fields, error_message). fields maps model field names to validated values."""
    try:
        payload = json.loads(request.body or b'{}')
    except ValueError:
        return None, 'Request body must be valid JSON.'
    if not isinstance(payload, dict):
        return None, 'Request body must be a JSON object.'
    fields = {}
    if 'selectedOption' in payload:
        option = payload['selectedOption']
        if option is not None and option not in OPTIONS:
            return None, 'selectedOption must be one of A, B, C, D or null.'
        fields['selected_option'] = option
    if 'markedForReview' in payload:
        if not isinstance(payload['markedForReview'], bool):
            return None, 'markedForReview must be true or false.'
        fields['marked_for_review'] = payload['markedForReview']
    if not fields:
        return None, 'Provide selectedOption and/or markedForReview.'
    return fields, None


def answer_detail(request, attempt_id, question_id):
    started = time.perf_counter()
    # Authentication comes first so anonymous callers always get 401, whatever the method.
    if not request.user.is_authenticated:
        return _error(401, 'AUTHENTICATION_REQUIRED', 'Please sign in to continue.')
    if request.method != 'PATCH':
        return _error(405, 'VALIDATION_ERROR', 'Only PATCH is supported on this endpoint.')
    # Design spec 3.6: Student operations verify role = STUDENT.
    if request.user.is_staff:
        return _error(403, 'FORBIDDEN', 'Only students can save exam answers.')

    attempt = Attempt.objects.select_related('exam').filter(pk=attempt_id).first()
    if attempt is None:
        return _error(404, 'ATTEMPT_NOT_FOUND', 'Attempt not found.')
    if attempt.student_id != request.user.id:
        return _error(403, 'FORBIDDEN', 'You do not have access to this attempt.')
    question = Question.objects.filter(pk=question_id, exam_id=attempt.exam_id).first()
    if question is None:
        return _error(404, 'QUESTION_NOT_FOUND', 'Question not found in this exam.')
    if attempt.status == Attempt.SUBMITTED:
        return _error(409, 'ATTEMPT_ALREADY_FINALIZED', 'This exam attempt has already been finalized.')
    fields, problem = _parse_payload(request)
    if problem:
        return _error(400, 'VALIDATION_ERROR', problem)
    fields['visited'] = True  # saving anything for a question means the student has been to it

    try:
        with transaction.atomic():
            # Lock is retained through the answer write; no late PATCH can slip in.
            attempt, _ = sync_attempt(attempt.pk)
            if not attempt.exam.is_available():
                return _error(403, 'EXAM_NOT_AVAILABLE', 'This exam is not currently available.')
            if attempt.status == Attempt.SUBMITTED:
                return _error(409, 'ATTEMPT_ALREADY_FINALIZED', 'This exam attempt has already been finalized.')
            answer, created = Answer.objects.get_or_create(attempt=attempt, question=question, defaults=fields)
            if not created:
                for name, value in fields.items():
                    setattr(answer, name, value)
                answer.save()
    except ValidationError:
        return _error(400, 'VALIDATION_ERROR', 'The answer could not be saved.')

    response = JsonResponse({
        'questionId': question.id,
        'selectedOption': answer.selected_option,
        'markedForReview': answer.marked_for_review,
        'displayState': answer.display_state,
        'savedAt': answer.saved_at.isoformat() if answer.saved_at else None,
    })
    response['Server-Timing'] = f'save;dur={(time.perf_counter() - started) * 1000:.1f}'
    return response
