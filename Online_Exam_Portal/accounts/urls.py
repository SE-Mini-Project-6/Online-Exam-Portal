from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.admin_login, name='login'),
    path('student-login/', views.student_login, name='student_login'),
    path('student-login/', views.student_login, name='student-login'),
    path('logout/', views.logout_view, name='logout'),

    # Role-aware dashboard URLs
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-submissions/', views.admin_submissions, name='admin_submissions'),
    path('admin-submissions/<int:exam_id>/release/', views.release_exam_results, name='release_exam_results'),
    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
]
