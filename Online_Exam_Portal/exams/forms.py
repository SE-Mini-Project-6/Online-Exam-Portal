from django import forms

from .models import Exam


class ExamForm(forms.ModelForm):
    start_at = forms.DateTimeField(
        widget=forms.DateTimeInput(
            format='%Y-%m-%dT%H:%M',
            attrs={'type': 'datetime-local'},
        ),
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S'],
    )
    end_at = forms.DateTimeField(
        widget=forms.DateTimeInput(
            format='%Y-%m-%dT%H:%M',
            attrs={'type': 'datetime-local'},
        ),
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S'],
    )

    class Meta:
        model = Exam
        fields = ('title', 'duration_minutes', 'start_at', 'end_at')

    def clean(self):
        cleaned_data = super().clean()
        start_at = cleaned_data.get('start_at')
        end_at = cleaned_data.get('end_at')
        duration_minutes = cleaned_data.get('duration_minutes')

        if start_at and end_at:
            if end_at <= start_at:
                self.add_error('end_at', 'End time must be after the start time.')
            elif duration_minutes is not None:
                window_minutes = (end_at - start_at).total_seconds() / 60
                if duration_minutes > window_minutes:
                    self.add_error('duration_minutes', 'Exam duration cannot exceed the availability window.')
        return cleaned_data
