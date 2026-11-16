"""
Forms for the accounts app.
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import Profile

MAX_AVATAR_SIZE = 2 * 1024 * 1024


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control', 'placeholder': 'Username',
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control', 'placeholder': 'Password',
        })


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control', 'placeholder': 'you@example.com',
    }))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control', 'placeholder': 'Username',
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control', 'placeholder': 'Password',
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control', 'placeholder': 'Confirm password',
        })

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            Profile.objects.get_or_create(user=user)
        return user


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(
        attrs={'class': 'form-control'}
    ))
    last_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(
        attrs={'class': 'form-control'}
    ))

    class Meta:
        model = Profile
        fields = ['bio', 'avatar']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'avatar': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
            }),
        }
        help_texts = {
            'avatar': 'Choose an image no larger than 2 MB.',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar and avatar.size > MAX_AVATAR_SIZE:
            raise ValidationError('The avatar must be no larger than 2 MB.')
        return avatar

    def save(self, commit=True):
        profile = super().save(commit=commit)
        if self.user:
            self.user.first_name = self.cleaned_data.get('first_name', '')
            self.user.last_name = self.cleaned_data.get('last_name', '')
            if commit:
                self.user.save()
        return profile


class SettingsForm(forms.ModelForm):
    """Preferences screen: theme, notifications, timezone."""

    TIMEZONE_CHOICES = [
        ('UTC', 'UTC'),
        ('Asia/Manila', 'Asia/Manila'),
        ('Asia/Singapore', 'Asia/Singapore'),
        ('America/New_York', 'America/New_York'),
    ]

    timezone = forms.ChoiceField(choices=TIMEZONE_CHOICES, widget=forms.Select(
        attrs={'class': 'form-control'}
    ))

    class Meta:
        model = Profile
        fields = ['dark_mode', 'email_notifications', 'timezone']
        widgets = {
            'dark_mode': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PasswordChangeCustomForm(PasswordChangeForm):
    """Change-password form used on the Settings screen."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({
            'class': 'form-control', 'placeholder': 'Current password',
        })
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control', 'placeholder': 'New password',
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control', 'placeholder': 'Confirm new password',
        })