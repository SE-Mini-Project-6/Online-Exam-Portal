from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
]

def home(request):
    """Home page showing role selection."""
    return render(request, 'core/home.html')