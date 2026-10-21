from django.core.exceptions import ValidationError
from django.db import models


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
