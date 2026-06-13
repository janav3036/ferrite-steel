from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required
def guide_home(request):
    return redirect('guide_core')

@login_required
def guide_core(request):
    return render(request, 'guide/core.html')

@login_required
def guide_quotations(request):
    return render(request, 'guide/quotations.html')

@login_required
def guide_training(request):
    return render(request, 'guide/training.html')