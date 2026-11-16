"""Request middleware for per-user timezone preferences."""

from zoneinfo import ZoneInfoNotFoundError

from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin


class ProfileTimezoneMiddleware(MiddlewareMixin):
    """Activate the signed-in user's saved timezone for the current request."""

    def process_request(self, request):
        timezone.deactivate()
        if not request.user.is_authenticated:
            return

        try:
            profile_timezone = request.user.profile.timezone
            timezone.activate(profile_timezone)
        except (AttributeError, ZoneInfoNotFoundError, ValueError):
            # Older accounts or stale preference values should not break pages.
            timezone.deactivate()

    def process_response(self, request, response):
        # Do not let one request's preference leak into another request.
        timezone.deactivate()
        return response
