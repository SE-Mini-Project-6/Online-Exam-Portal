from django.urls import path

from . import api

app_name = 'api'

urlpatterns = [
    path('attempts/<int:attempt_id>/answers/<int:question_id>', api.answer_detail, name='answer_detail'),
]
