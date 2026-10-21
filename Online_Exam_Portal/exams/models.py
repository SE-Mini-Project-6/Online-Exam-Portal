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

