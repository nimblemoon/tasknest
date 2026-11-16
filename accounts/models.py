"""
Models for the accounts app (auth-related vertical slice).
"""
from django.conf import settings
from django.db import models


class Profile(models.Model):
    """Extends the built-in User with app-specific profile + settings info.

    Stats shown on the Profile screen (e.g. tasks completed this week)
    are computed on the fly in the view rather than stored here, since
    they are derived from the tasks app and would otherwise go stale.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    bio = models.CharField(max_length=255, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # --- Settings screen fields ---
    dark_mode = models.BooleanField(default=False)
    email_notifications = models.BooleanField(default=True)
    timezone = models.CharField(max_length=50, default='UTC')

    def __str__(self):
        return f'Profile for {self.user.username}'