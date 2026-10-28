"""Server-authoritative attempt timeouts and exactly-once grading for Sprint 2 #22."""
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models import Attempt


def sync_attempt(attempt_id, *, now=None, manual=False):
    """Get (attempt, finalized_now). Deadline and score are controlled by server.

    Answer writers must call this inside their own atomic transaction, so the
    row lock is retained until their answer update is committed.
    """
    now = now or timezone.now()
    with transaction.atomic():
        attempt = (Attempt.objects.select_related('exam')
                   .select_for_update().get(pk=attempt_id))
        if attempt.status == Attempt.SUBMITTED:
            return attempt, False

        changed = []
        if attempt.started_at is None:
            # Historic Sprint-1 rows have no recorded first-access timestamp.
            attempt.started_at = now
            changed.append('started_at')
        bound = min(
            attempt.started_at + timedelta(minutes=attempt.exam.duration_minutes),
            attempt.exam.end_at,
        )
        # A shorter admin availability window can shorten but not extend time.
        if attempt.deadline_at is None or bound < attempt.deadline_at:
            attempt.deadline_at = bound
            changed.append('deadline_at')
        if changed:
            attempt.save(update_fields=changed)

        expired = now >= attempt.deadline_at
        if not expired and not (manual and attempt.exam.is_available(now)):
            return attempt, False

        attempt.score = sum(
            1 for ans in attempt.answers.select_related('question')
            if ans.question.exam_id == attempt.exam_id
            and ans.selected_option == ans.question.correct_option
        )
        attempt.status = Attempt.SUBMITTED
        attempt.submitted_at = now
        attempt.save(update_fields=['score', 'status', 'submitted_at'])
        return attempt, True
