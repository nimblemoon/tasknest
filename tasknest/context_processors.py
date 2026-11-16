"""Template context shared by every signed-in screen (sidebar + quick add)."""
from django.utils import timezone

from accounts.models import Profile
from tasks.forms import QuickAddForm
from tasks.models import Project


def workspace(request):
    if not request.user.is_authenticated:
        return {'profile': None}

    profile, _ = Profile.objects.get_or_create(user=request.user)
    return {
        'profile': profile,
        'nav_projects': Project.objects.filter(
            owner=request.user, is_archived=False,
        ),
        'quick_add_form': QuickAddForm(user=request.user),
        'nav_today': timezone.localdate(),
    }
