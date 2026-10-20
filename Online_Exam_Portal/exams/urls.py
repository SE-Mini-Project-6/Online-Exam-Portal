from django.urls import path

from . import views

app_name = 'exams'

urlpatterns = [
    path('', views.available_exams, name='list'),
    path('available/', views.available_exams, name='available'),
    path('create/', views.create_exam, name='create'),
    path('<int:exam_id>/', views.take_exam, name='detail'),
    path('<int:exam_id>/take/', views.take_exam, name='take'),
]

