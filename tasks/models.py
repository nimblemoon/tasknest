# tasks/models.py
"""
Models for the tasks app: Projects, Tasks, and Subtasks.

Projects give tasks a home (a course, a client, a personal goal). Subtasks
turn a large task into a checklist. Both are intentionally lightweight so the
dashboard can stay fast while still feeling like a real workspace.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone


class Project(models.Model):
    """A colour-coded container for related tasks."""

    class Color(models.TextChoices):
        EMERALD = 'emerald', 'Emerald'
        CORAL = 'coral', 'Coral'
        AMBER = 'amber', 'Amber'
        BLUE = 'blue', 'Blue'
        VIOLET = 'violet', 'Violet'
        SLATE = 'slate', 'Slate'

    COLOR_HEX = {
        Color.EMERALD: '#2F7A5F',
        Color.CORAL: '#D9603F',
        Color.AMBER: '#C08A18',
        Color.BLUE: '#3B6FB6',
        Color.VIOLET: '#7A5AB8',
        Color.SLATE: '#5B6B73',
    }

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='projects',
    )
    name = models.CharField(max_length=100)
    code = models.CharField(
        max_length=8,
        blank=True,
        help_text='Short label shown on task rows, e.g. CS101.',
    )
    description = models.CharField(max_length=255, blank=True)
    color = models.CharField(
        max_length=12,
        choices=Color.choices,
        default=Color.EMERALD,
    )
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['is_archived', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['owner', 'name'],
                name='unique_project_name_per_owner',
            ),
        ]

    def __str__(self):
        return self.name

    @property
    def color_hex(self):
        return self.COLOR_HEX.get(self.color, self.COLOR_HEX[self.Color.EMERALD])

    @property
    def label(self):
        return self.code or self.name[:10]

    @property
    def total_tasks(self):
        return self.tasks.count()

    @property
    def open_tasks(self):
        return self.tasks.filter(is_complete=False).count()

    @property
    def done_tasks(self):
        return self.tasks.filter(is_complete=True).count()

    @property
    def progress_percent(self):
        total = self.total_tasks
        if not total:
            return 0
        return round(self.done_tasks * 100 / total)


class Tag(models.Model):
    """A free-form label that can be attached to many tasks."""

    class Color(models.TextChoices):
        EMERALD = 'emerald', 'Emerald'
        CORAL = 'coral', 'Coral'
        AMBER = 'amber', 'Amber'
        BLUE = 'blue', 'Blue'
        VIOLET = 'violet', 'Violet'
        SLATE = 'slate', 'Slate'

    COLOR_HEX = Project.COLOR_HEX

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tags',
    )
    name = models.CharField(max_length=40)
    color = models.CharField(
        max_length=12,
        choices=Color.choices,
        default=Color.EMERALD,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['owner', 'name'],
                name='unique_tag_name_per_owner',
            ),
        ]

    def __str__(self):
        return self.name

    @property
    def color_hex(self):
        return self.COLOR_HEX.get(self.color, self.COLOR_HEX[Project.Color.EMERALD])


class Task(models.Model):
    """A single to-do item belonging to a user.

    A task may belong to a project and may contain subtasks. The due date is
    optional so "someday" work can live in the list without a fake deadline.
    """

    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tasks',
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks',
    )
    tags = models.ManyToManyField(
        'Tag',
        blank=True,
        related_name='tasks',
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    is_complete = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['due_date']
        indexes = [
            models.Index(fields=['owner', 'is_complete', 'due_date']),
            models.Index(fields=['owner', 'is_pinned']),
        ]

    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        """A task is overdue if its due date has passed and it isn't done."""
        return (
            not self.is_complete
            and self.due_date is not None
            and self.due_date < timezone.now()
        )

    @property
    def due_bucket(self):
        """Coarse bucket used by the board and dashboard grouping."""
        if self.is_complete:
            return 'done'
        if self.due_date is None:
            return 'someday'
        local_due = timezone.localtime(self.due_date)
        day_delta = (local_due.date() - timezone.localdate()).days
        if self.is_overdue or day_delta < 0:
            return 'overdue'
        if day_delta == 0:
            return 'today'
        if day_delta == 1:
            return 'tomorrow'
        if day_delta <= 7:
            return 'week'
        return 'later'

    @property
    def humanized_due(self):
        """Plain-language due text: 'Due today, 3:00 PM', 'Overdue by 2 days',
        'Due tomorrow', 'Due in 5 days', or a plain date once it's far out.
        """
        if self.is_complete:
            completed_local = (
                timezone.localtime(self.completed_at)
                if self.completed_at
                else (timezone.localtime(self.due_date) if self.due_date else timezone.localtime())
            )
            return f'Completed {completed_local.strftime("%b %d").replace(" 0", " ")}'

        if self.due_date is None:
            return 'No deadline'

        now = timezone.now()
        local_due = timezone.localtime(self.due_date)
        local_now = timezone.localtime(now)
        day_delta = (local_due.date() - local_now.date()).days
        # Use %I (zero-padded) then strip the leading zero manually —
        # %-I is Linux/Mac only and raises ValueError on Windows.
        time_str = local_due.strftime('%I:%M %p').lstrip('0')

        if self.is_overdue:
            overdue_days = -day_delta
            if overdue_days <= 0:
                return f'Overdue, was due today at {time_str}'
            if overdue_days == 1:
                return 'Overdue by 1 day'
            return f'Overdue by {overdue_days} days'

        if day_delta == 0:
            return f'Due today, {time_str}'
        if day_delta == 1:
            return 'Due tomorrow'
        if 2 <= day_delta <= 6:
            return f'Due in {day_delta} days'
        return f'Due {local_due.strftime("%b %d").replace(" 0", " ")}'

    @property
    def due_tone(self):
        if self.is_complete:
            return 'done'
        if self.due_date is None:
            return 'quiet'
        if self.is_overdue:
            return 'danger'
        if self.due_bucket == 'today':
            return 'warn'
        return 'quiet'

    @property
    def subtask_total(self):
        return self.subtasks.count()

    @property
    def subtask_done(self):
        return self.subtasks.filter(is_done=True).count()

    @property
    def subtask_percent(self):
        total = self.subtask_total
        if not total:
            return 0
        return round(self.subtask_done * 100 / total)

    def mark_complete(self):
        """Mark this task as finished and stamp the completion time."""
        self.is_complete = True
        self.completed_at = timezone.now()
        self.save(update_fields=['is_complete', 'completed_at', 'updated_at'])

    def mark_incomplete(self):
        """Revert a completed task back to pending."""
        self.is_complete = False
        self.completed_at = None
        self.save(update_fields=['is_complete', 'completed_at', 'updated_at'])


class Subtask(models.Model):
    """A checklist item inside a task."""

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='subtasks',
    )
    title = models.CharField(max_length=200)
    is_done = models.BooleanField(default=False)
    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['position', 'created_at']

    def __str__(self):
        return self.title
