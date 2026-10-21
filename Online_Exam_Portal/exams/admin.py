from django.contrib import admin

from .models import Exam


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'duration_minutes', 'start_at', 'end_at')
    list_filter = ('start_at', 'end_at')
    search_fields = ('title',)
