"""
Views for the accounts app: Register, Login, Logout, Profile, Settings, Theme.
"""
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from tasks.models import Task
from tasks.utils import completion_streak

from .forms import ProfileForm, RegisterForm, LoginForm, SettingsForm, PasswordChangeCustomForm
from .models import Profile


def register_view(request):
    if request.user.is_authenticated:
        return redirect('tasks:dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created. You can now log in.')
            return redirect('accounts:login')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


class TaskNestLoginView(LoginView):
    form_class = LoginForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True


class TaskNestLogoutView(LogoutView):
    next_page = 'accounts:login'


@login_required
def profile_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=profile, user=request.user)

    week_ago = timezone.now() - timezone.timedelta(days=7)
    week_tasks = Task.objects.filter(owner=request.user)
    stats = {
        'completed_this_week': week_tasks.filter(
            is_complete=True, completed_at__gte=week_ago,
        ).count(),
        'total_pending': week_tasks.filter(is_complete=False).count(),
        'total_tasks': week_tasks.count(),
        'overdue': week_tasks.filter(
            is_complete=False, due_date__lt=timezone.now(),
        ).count(),
        'streak': completion_streak(request.user),
    }

    return render(request, 'accounts/profile.html', {'form': form, 'stats': stats})


@login_required
def settings_view(request):
    """Preferences screen: dark mode, email notifications, timezone."""
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = SettingsForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Settings saved.')
            return redirect('accounts:settings')
    else:
        form = SettingsForm(instance=profile)

    return render(request, 'accounts/settings.html', {'form': form, 'profile': profile})


@login_required
def change_password_view(request):
    """Change-password form, kept on its own URL and linked from Settings."""
    if request.method == 'POST':
        form = PasswordChangeCustomForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # keep the user logged in
            messages.success(request, 'Password changed successfully.')
            return redirect('accounts:settings')
    else:
        form = PasswordChangeCustomForm(user=request.user)

    return render(request, 'accounts/change_password.html', {'form': form})


@login_required
@require_POST
def theme_toggle_view(request):
    """Flip the user's theme from the top bar and return to the same page."""
    profile, _ = Profile.objects.get_or_create(user=request.user)
    profile.dark_mode = not profile.dark_mode
    profile.save(update_fields=['dark_mode'])

    target = request.POST.get('next')
    if not target or not url_has_allowed_host_and_scheme(
        target,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        target = reverse('tasks:dashboard')
    return HttpResponseRedirect(target)
