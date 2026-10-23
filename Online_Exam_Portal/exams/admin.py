from django.contrib import admin

from .models import Exam, Question


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    inlines = [QuestionInline]
    list_display = ('title', 'duration_minutes', 'start_at', 'end_at')
    list_filter = ('start_at', 'end_at')
    search_fields = ('title',)
