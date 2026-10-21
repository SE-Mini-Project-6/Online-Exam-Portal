from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render

from .forms import ExamForm


@login_required
def create_exam(request):
    if not request.user.is_staff:
        return HttpResponseForbidden("You don't have access to exam configuration.")

    if request.method == 'POST':
        form = ExamForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('accounts:admin_dashboard')
    else:
        form = ExamForm()

    return render(request, 'exams/create_exam.html', {'form': form})
