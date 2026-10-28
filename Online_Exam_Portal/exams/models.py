from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Exam(models.Model):
    title = models.CharField(max_length=200)
    duration_minutes = models.PositiveIntegerField()
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('start_at', 'title')

    def __str__(self):
        return self.title

    def clean(self):
        errors = {}
        if self.duration_minutes is not None and self.duration_minutes < 1:
            errors['duration_minutes'] = 'Duration must be at least one minute.'
        if self.start_at and self.end_at:
            if self.end_at <= self.start_at:
                errors['end_at'] = 'End time must be after the start time.'
            elif self.duration_minutes is not None:
                window_minutes = (self.end_at - self.start_at).total_seconds() / 60
                if self.duration_minutes > window_minutes:
                    errors['duration_minutes'] = 'Exam duration cannot exceed the availability window.'
        if errors:
            raise ValidationError(errors)

    def is_available(self, current_time=None):
        """Check if exam is within its configured availability window."""
        if current_time is None:
            current_time = timezone.now()
        return self.start_at <= current_time <= self.end_at

    def is_upcoming(self, current_time=None):
        """Check if exam has not started yet."""
        if current_time is None:
            current_time = timezone.now()
        return current_time < self.start_at

    def is_expired(self, current_time=None):
        """Check if exam window has already closed."""
        if current_time is None:
            current_time = timezone.now()
        return current_time > self.end_at

    def get_status(self, current_time=None):
        """Return status string: 'available', 'upcoming', or 'expired'."""
        if self.is_available(current_time):
            return 'available'
        elif self.is_upcoming(current_time):
            return 'upcoming'
        return 'expired'

    def get_status_label(self, current_time=None):
        """Return human-readable status badge label."""
        status = self.get_status(current_time)
        if status == 'available':
            return 'Available Now'
        elif status == 'upcoming':
            return 'Upcoming'
        return 'Closed'

    @property
    def is_currently_available(self):
        return self.is_available()

    @property
    def is_currently_upcoming(self):
        return self.is_upcoming()

    @property
    def is_currently_expired(self):
        return self.is_expired()

    @property
    def status(self):
        return self.get_status()

    @property
    def status_label(self):
        return self.get_status_label()



class Question(models.Model):
    OPTION_CHOICES = [('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')]

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    option_a = models.CharField(max_length=300)
    option_b = models.CharField(max_length=300)
    option_c = models.CharField(max_length=300)
    option_d = models.CharField(max_length=300)
    correct_option = models.CharField(max_length=1, choices=OPTION_CHOICES)

    class Meta:
        ordering = ('id',)

    def __str__(self):
        return self.text[:60]

    def options(self):
        """Return (key, text) pairs in display order."""
        return [('A', self.option_a), ('B', self.option_b), ('C', self.option_c), ('D', self.option_d)]

    def clean(self):
        errors = {}
        if not self.text or not self.text.strip():
            errors['text'] = 'Question text is required.'
        for field in ('option_a', 'option_b', 'option_c', 'option_d'):
            if not getattr(self, field, None) or not getattr(self, field).strip():
                errors[field] = 'All four options must be non-empty.'
        if self.correct_option not in ('A', 'B', 'C', 'D'):
            errors['correct_option'] = 'Select exactly one correct option (A, B, C, or D).'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)



# Sprint 1: persistent per-student attempts and immutable submitted scores.
from django.conf import settings


class Attempt(models.Model):
    IN_PROGRESS = 'in_progress'
    SUBMITTED = 'submitted'
    STATUS_CHOICES = [(IN_PROGRESS, 'In progress'), (SUBMITTED, 'Submitted')]

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='exam_attempts')
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=IN_PROGRESS)
    score = models.PositiveIntegerField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['exam', 'student'], name='unique_student_exam_attempt')]

    def __str__(self):
        return f'{self.student} - {self.exam} ({self.status})'


class Answer(models.Model):
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='student_answers')
    selected_option = models.CharField(max_length=1, choices=Question.OPTION_CHOICES, null=True, blank=True)
    marked_for_review = models.BooleanField(default=False)
    visited = models.BooleanField(default=False)
    saved_at = models.DateTimeField(auto_now=True, null=True)

    # The five question-grid states (design spec 4.6) and their display labels.
    STATE_LABELS = {
        'NOT_VISITED': 'Not Visited',
        'NOT_ANSWERED': 'Not Answered',
        'ANSWERED': 'Answered',
        'MARKED_FOR_REVIEW': 'Marked for Review',
        'ANSWERED_MARKED_FOR_REVIEW': 'Answered & Marked for Review',
    }

    class Meta:
        constraints = [models.UniqueConstraint(fields=['attempt', 'question'], name='unique_attempt_question_answer')]

    @property
    def display_state(self):
        """Exactly one grid state per question; the review flag is independent of the answer."""
        answered = self.selected_option is not None
        if self.marked_for_review:
            return 'ANSWERED_MARKED_FOR_REVIEW' if answered else 'MARKED_FOR_REVIEW'
        if answered:
            return 'ANSWERED'
        return 'NOT_ANSWERED' if self.visited else 'NOT_VISITED'

    def clean(self):
        errors = {}
        if self.question_id and self.attempt_id and self.question.exam_id != self.attempt.exam_id:
            errors['question'] = 'Question does not belong to this attempt exam.'
        if self.selected_option is not None and self.selected_option not in ('A', 'B', 'C', 'D'):
            errors['selected_option'] = 'Choose one of A, B, C, or D.'
        if self.attempt_id and self.attempt.status == Attempt.SUBMITTED:
            errors['attempt'] = 'Answers cannot be changed after submission.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
