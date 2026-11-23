"""
Forms for the tasks app.
"""
from datetime import timedelta

from django import forms
from django.utils import timezone

from .models import Project, Subtask, Tag, Task, TaskComment


DATETIME_INPUT_FORMAT = '%Y-%m-%dT%H:%M'


def _datetime_widget(placeholder=None):
    attrs = {
        'class': 'form-control',
        'type': 'datetime-local',
        'data-datetime': 'true',
    }
    if placeholder:
        attrs['placeholder'] = placeholder
    return forms.DateTimeInput(attrs=attrs, format=DATETIME_INPUT_FORMAT)


class ProjectForm(forms.ModelForm):
    """Create or edit a colour-coded project."""

    class Meta:
        model = Project
        fields = ['name', 'code', 'description', 'color', 'is_archived']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Capstone Project',
                'autofocus': True,
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. CS101',
                'maxlength': 8,
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'What is this project about?',
            }),
            'color': forms.RadioSelect(attrs={'class': 'color-radio'}),
            'is_archived': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if not name:
            raise forms.ValidationError('Give the project a name.')

        duplicates = Project.objects.filter(owner=self.user, name__iexact=name)
        if self.instance.pk:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise forms.ValidationError('You already have a project with that name.')
        return name

    def clean_code(self):
        return self.cleaned_data.get('code', '').strip().upper()


class TaskForm(forms.ModelForm):
    """Shared form for both creating and editing a Task."""

    due_date = forms.DateTimeField(
        required=False,
        widget=_datetime_widget(),
        input_formats=[DATETIME_INPUT_FORMAT, '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M'],
        help_text='Leave blank for a task without a deadline.',
    )

    class Meta:
        model = Task
        fields = ['title', 'description', 'project', 'tags', 'due_date', 'priority', 'recurrence', 'recurrence_interval', 'recurrence_end_date']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Finish CS homework',
                'autofocus': True,
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Optional notes, links, or context...',
            }),
            'project': forms.Select(attrs={'class': 'form-control'}),
            'tags': forms.SelectMultiple(attrs={'class': 'form-control', 'size': '4'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'recurrence': forms.Select(attrs={'class': 'form-control'}),
            'recurrence_interval': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'recurrence_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        projects = Project.objects.filter(owner=user, is_archived=False)
        self.fields['project'].queryset = projects
        self.fields['project'].required = False
        self.fields['project'].empty_label = 'No project'
        self.fields['tags'].queryset = Tag.objects.filter(owner=user)
        self.fields['tags'].required = False
        self.fields['priority'].help_text = (
            'High priority tasks are flagged first on the dashboard.'
        )

    def clean(self):
        cleaned = super().clean()
        recurrence = cleaned.get('recurrence') or 'none'
        due_date = cleaned.get('due_date')
        if recurrence != 'none' and not due_date:
            self.add_error('due_date', 'Recurring tasks need a due date.')
        interval = cleaned.get('recurrence_interval')
        if interval is not None and interval < 1:
            self.add_error('recurrence_interval', 'Interval must be at least 1.')
        return cleaned


class QuickAddForm(forms.ModelForm):
    """Compact form used by the global quick-add dialog."""

    due_date = forms.DateTimeField(
        required=False,
        widget=_datetime_widget(),
        input_formats=[DATETIME_INPUT_FORMAT, '%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M'],
    )

    class Meta:
        model = Task
        fields = ['title', 'due_date', 'priority', 'project']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'What needs to get done?',
                'autocomplete': 'off',
                'autofocus': True,
            }),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'project': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields['project'].queryset = Project.objects.filter(
            owner=user, is_archived=False,
        )
        self.fields['project'].required = False
        self.fields['project'].empty_label = 'No project'
        if not self.is_bound and not self.initial.get('due_date'):
            local_now = timezone.localtime()
            default_due = local_now.replace(hour=17, minute=0, second=0, microsecond=0)
            if default_due < local_now:
                default_due += timedelta(days=1)
            self.initial['due_date'] = default_due


class SubtaskForm(forms.ModelForm):
    class Meta:
        model = Subtask
        fields = ['title']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Add a step...',
                'autocomplete': 'off',
                'maxlength': 200,
            }),
        }


class DashboardFilterForm(forms.Form):
    """Validated controls for the dashboard's smart views and search."""

    VIEW_CHOICES = [
        ('all', 'All'),
        ('today', 'Today'),
        ('upcoming', 'Upcoming'),
        ('overdue', 'Overdue'),
        ('someday', 'No date'),
        ('completed', 'Completed'),
    ]
    PRIORITY_CHOICES = [('', 'Any priority')] + list(Task.Priority.choices)
    SORT_CHOICES = [
        ('due', 'Due date (soonest)'),
        ('-priority', 'Priority (highest)'),
        ('-created', 'Newest first'),
        ('title', 'Title (A–Z)'),
    ]

    view = forms.ChoiceField(
        choices=VIEW_CHOICES, required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICES, required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    sort = forms.ChoiceField(
        choices=SORT_CHOICES, required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    q = forms.CharField(
        required=False, max_length=120,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search tasks...',
            'autocomplete': 'off',
        }),
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields['project'] = forms.ModelChoiceField(
            queryset=Project.objects.filter(owner=user, is_archived=False),
            required=False,
            empty_label='All projects',
            widget=forms.Select(attrs={'class': 'form-control'}),
        )
        self.fields['tag'] = forms.ModelChoiceField(
            queryset=Tag.objects.filter(owner=user),
            required=False,
            empty_label='All tags',
            widget=forms.Select(attrs={'class': 'form-control'}),
        )

    def project_id(self):
        project = self.cleaned_data.get('project') if self.is_valid() else None
        return project.pk if project else ''


class TagForm(forms.ModelForm):
    """Create or edit a label."""

    class Meta:
        model = Tag
        fields = ['name', 'color']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Study, Errand',
                'autofocus': True,
            }),
            'color': forms.RadioSelect(attrs={'class': 'color-radio'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if not name:
            raise forms.ValidationError('Give the tag a name.')
        duplicates = Tag.objects.filter(owner=self.user, name__iexact=name)
        if self.instance.pk:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise forms.ValidationError('You already have a tag with that name.')
        return name


class CommentForm(forms.ModelForm):
    class Meta:
        model = TaskComment
        fields = ['body']
        widgets = {
            'body': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Add a note, link, or update...',
            }),
        }

    def clean_body(self):
        body = self.cleaned_data['body'].strip()
        if not body:
            raise forms.ValidationError('Write something first.')
        return body
