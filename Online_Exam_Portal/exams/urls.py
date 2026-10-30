from django.urls import path

from . import views, sprint1_views

app_name = 'exams'

urlpatterns = [
    path('', views.available_exams, name='list'),
    path('available/', views.available_exams, name='available'),
    path('create/', views.create_exam, name='create'),
    path('<int:exam_id>/', views.take_exam, name='detail'),
    path('<int:exam_id>/take/', views.take_exam, name='take'),
    path('<int:exam_id>/submit/', sprint1_views.submit_exam, name='submit'),
    path('<int:exam_id>/result/', views.student_result, name='result'),
    path('<int:exam_id>/questions/', sprint1_views.question_list, name='questions'),
    path('<int:exam_id>/questions/add/', sprint1_views.question_create, name='question_create'),
    path('<int:exam_id>/questions/<int:question_id>/edit/', sprint1_views.question_edit, name='question_edit'),
    path('<int:exam_id>/questions/<int:question_id>/delete/', sprint1_views.question_delete, name='question_delete'),
]

