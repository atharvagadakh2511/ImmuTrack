from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import ParentRegistrationForm
from .models import Role

def register_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard_redirect')
        
    if request.method == 'POST':
        form = ParentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            user.profile.role = Role.PARENT
            user.profile.phone_number = form.cleaned_data['phone_number']
            user.profile.save()
            login(request, user)
            messages.success(request, 'Account created successfully! Welcome to ImmuTrack.')
            return redirect('accounts:dashboard_redirect')
    else:
        form = ParentRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard_redirect')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.info(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect('accounts:dashboard_redirect')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:login')

@login_required
def dashboard_redirect_view(request):
    profile = request.user.profile
    if profile.is_admin:
        return redirect('analytics:admin_dashboard')
    elif profile.is_health_worker:
        return redirect('vaccination:worker_dashboard')
    else:
        return redirect('children:parent_dashboard')
