from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.utils import timezone
from PIL import Image

from .forms import MAX_AVATAR_SIZE, ProfileForm, SettingsForm
from .models import Profile
from tasknest.middleware import ProfileTimezoneMiddleware


class ProfileFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='safe-password')

    @staticmethod
    def png_file(extra_bytes=0):
        image_buffer = BytesIO()
        Image.new('RGB', (1, 1), color='navy').save(image_buffer, format='PNG')
        image_bytes = image_buffer.getvalue() + (b'x' * extra_bytes)
        return SimpleUploadedFile('avatar.png', image_bytes, content_type='image/png')

    def test_accepts_valid_avatar_within_size_limit(self):
        form = ProfileForm(
            data={'bio': '', 'first_name': '', 'last_name': ''},
            files={'avatar': self.png_file()},
            user=self.user,
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_rejects_avatar_larger_than_two_megabytes(self):
        valid_png = self.png_file()
        extra_bytes = MAX_AVATAR_SIZE - valid_png.size + 1
        form = ProfileForm(
            data={'bio': '', 'first_name': '', 'last_name': ''},
            files={'avatar': self.png_file(extra_bytes=extra_bytes)},
            user=self.user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('avatar', form.errors)
        self.assertIn('no larger than 2 MB', form.errors['avatar'][0])

    def test_rejects_non_image_avatar(self):
        form = ProfileForm(
            data={'bio': '', 'first_name': '', 'last_name': ''},
            files={'avatar': SimpleUploadedFile(
                'avatar.txt', b'not an image', content_type='image/png',
            )},
            user=self.user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('avatar', form.errors)


class SettingsFormTests(TestCase):
    def test_timezone_choice_is_saved(self):
        profile = Profile.objects.create(user=User.objects.create_user(
            username='bob', password='safe-password',
        ))
        form = SettingsForm(
            data={
                'dark_mode': 'on',
                'email_notifications': 'on',
                'timezone': 'Asia/Manila',
            },
            instance=profile,
        )

        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        profile.refresh_from_db()
        self.assertEqual(profile.timezone, 'Asia/Manila')

    def test_rejects_timezone_outside_supported_choices(self):
        form = SettingsForm(data={'timezone': 'Not/A_Timezone'})

        self.assertFalse(form.is_valid())
        self.assertIn('timezone', form.errors)


class ProfileTimezoneMiddlewareTests(TestCase):
    def test_activates_profile_timezone_for_authenticated_request(self):
        user = User.objects.create_user(username='carol', password='safe-password')
        Profile.objects.create(user=user, timezone='Asia/Manila')
        request = RequestFactory().get('/')
        request.user = user
        middleware = ProfileTimezoneMiddleware(
            lambda request: HttpResponse(timezone.get_current_timezone_name())
        )

        response = middleware(request)

        self.assertEqual(response.content, b'Asia/Manila')
        self.assertEqual(timezone.get_current_timezone_name(), 'UTC')

    def test_missing_profile_falls_back_without_failing_request(self):
        user = User.objects.create_user(username='legacy', password='safe-password')
        request = RequestFactory().get('/')
        request.user = user
        middleware = ProfileTimezoneMiddleware(
            lambda request: HttpResponse(timezone.get_current_timezone_name())
        )

        response = middleware(request)

        self.assertEqual(response.content, b'UTC')
