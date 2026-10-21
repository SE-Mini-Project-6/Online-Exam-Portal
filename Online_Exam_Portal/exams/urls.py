from django.urls import path

from . import views

app_name = 'exams'

urlpatterns = [
    path('create/', views.create_exam, name='create'),
]
