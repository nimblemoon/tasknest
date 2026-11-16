#tasks/models.py
"""
Models for the tasks app (core task-management vertical slice).
"""
from django.conf import settings
from django.db import models
from django.utils import timezone


class Task(models.Model):
    """A single to-do item belonging to a user.

    Sorting/filtering by due date and priority (Objectives O2, O4) is
    driven by the `due_date` and `priority` fields below.
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
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateTimeField()
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    is_complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['due_date']

    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        """A task is overdue if its due date has passed and it isn't done."""
        return (not self.is_complete) and self.due_date < timezone.now()

    @property
    def humanized_due(self):
        """Plain-language due text: 'Due today, 3:00 PM', 'Overdue by 2 days',
        'Due tomorrow', 'Due in 5 days', or a plain date once it's far out.

        Dashboard rows lead with this instead of a raw timestamp, since
        relative time is what a student actually needs to act on.
        """
        now = timezone.now()
        local_due = timezone.localtime(self.due_date)
        local_now = timezone.localtime(now)
        day_delta = (local_due.date() - local_now.date()).days
        # Use %I (zero-padded) then strip the leading zero manually —
        # %-I is Linux/Mac only and raises ValueError on Windows.
        time_str = local_due.strftime('%I:%M %p').lstrip('0')

        if self.is_complete:
            completed_local = timezone.localtime(self.completed_at) if self.completed_at else local_due
            return f'Completed {completed_local.strftime("%b %d").replace(" 0", " ")}'

        if self.is_overdue:
            overdue_days = -day_delta
            if overdue_days <= 0:
                return f'Overdue, was due today at {time_str}'
            elif overdue_days == 1:
                return 'Overdue by 1 day'
            return f'Overdue by {overdue_days} days'

        if day_delta == 0:
            return f'Due today, {time_str}'
        if day_delta == 1:
            return 'Due tomorrow'
        if 2 <= day_delta <= 6:
            return f'Due in {day_delta} days'
        return f'Due {local_due.strftime("%b %d").replace(" 0", " ")}'

    def mark_complete(self):
        """Mark this task as finished and stamp the completion time."""
        self.is_complete = True
        self.completed_at = timezone.now()
        self.save(update_fields=['is_complete', 'completed_at'])

    def mark_incomplete(self):
        """Revert a completed task back to pending."""
        self.is_complete = False
        self.completed_at = None
        self.save(update_fields=['is_complete', 'completed_at'])
