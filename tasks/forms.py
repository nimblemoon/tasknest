"""
Forms for the tasks app.
"""
from django import forms

from .models import Task


class TaskForm(forms.ModelForm):
    """Shared form for both creating and editing a Task (O1)."""

    class Meta:
        model = Task
        fields = ['title', 'description', 'due_date', 'priority']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Finish CS homework',
                'autofocus': True,
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional details...',
            }),
            'due_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
            }),
            'priority': forms.Select(attrs={'class': 'form-control'}),
        }


class TaskFilterForm(forms.Form):
    """Non-model form powering the Filter/Sort view (O4)."""

    STATUS_CHOICES = [
        ('', 'All statuses'),
        ('pending', 'Pending'),
        ('completed', 'Completed'),
    ]
    PRIORITY_CHOICES = [('', 'All priorities')] + list(Task.Priority.choices)
    SORT_CHOICES = [
        ('due_date', 'Due date (soonest first)'),
        ('-priority', 'Priority (highest first)'),
    ]

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control sleek-select'}),
    )
    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control sleek-select'}),
    )
    sort = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control sleek-select'}),
    )
