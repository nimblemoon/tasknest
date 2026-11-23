"""
Shared helpers for the tasks app: filtering, grouping, calendar, insights.

Keeping this logic out of the views means the dashboard, board, calendar and
insights screens all agree on what "overdue" or "this week" means.
"""
import calendar
from collections import OrderedDict, defaultdict
from datetime import date, timedelta

from django.db.models import Case, Count, F, IntegerField, Q, When
from django.utils import timezone

from .models import FocusSession, Project, Task

_PRIORITY_WEIGHT = {'high': 3, 'medium': 2, 'low': 1}

_PRIORITY_CASE = Case(
    *[When(priority=key, then=value) for key, value in _PRIORITY_WEIGHT.items()],
    output_field=IntegerField(),
)


def base_task_queryset(user):
    """Tasks for one user, with related rows fetched up front."""
    return (
        Task.objects.filter(owner=user)
        .select_related('project')
        .prefetch_related('subtasks', 'tags')
    )


def apply_task_filters(
    queryset,
    view='all',
    priority='',
    project_id=None,
    tag_id=None,
    q='',
    sort='due',
):
    """Apply the dashboard's smart view, search, project and sort controls."""
    today = timezone.localdate()
    now = timezone.now()

    if view == 'completed':
        queryset = queryset.filter(is_complete=True)
    elif view == 'overdue':
        queryset = queryset.filter(is_complete=False, due_date__lt=now)
    elif view == 'today':
        queryset = queryset.filter(is_complete=False, due_date__date=today)
    elif view == 'upcoming':
        queryset = queryset.filter(is_complete=False, due_date__date__gt=today)
    elif view == 'someday':
        queryset = queryset.filter(is_complete=False, due_date__isnull=True)
    else:
        queryset = queryset.filter(is_complete=False)

    if priority in ('low', 'medium', 'high'):
        queryset = queryset.filter(priority=priority)

    if project_id:
        queryset = queryset.filter(project_id=project_id)

    if tag_id:
        queryset = queryset.filter(tags__id=tag_id)

    if q:
        queryset = queryset.filter(
            Q(title__icontains=q)
            | Q(description__icontains=q)
            | Q(project__name__icontains=q)
            | Q(subtasks__title__icontains=q)
            | Q(tags__name__icontains=q)
            | Q(comments__body__icontains=q)
        ).distinct()

    queryset = queryset.annotate(_priority_weight=_PRIORITY_CASE)

    if sort == '-priority':
        ordering = ['-is_pinned', '-_priority_weight', F('due_date').asc(nulls_last=True)]
    elif sort == '-created':
        ordering = ['-is_pinned', '-created_at']
    elif sort == 'title':
        ordering = ['-is_pinned', 'title']
    else:
        ordering = ['-is_pinned', F('due_date').asc(nulls_last=True), '-_priority_weight']

    return queryset.order_by(*ordering)


GROUP_LABELS = OrderedDict([
    ('pinned', 'Pinned'),
    ('overdue', 'Overdue'),
    ('today', 'Today'),
    ('tomorrow', 'Tomorrow'),
    ('week', 'This week'),
    ('later', 'Later'),
    ('someday', 'No deadline'),
    ('done', 'Completed'),
])


def group_tasks(tasks):
    """Group an iterable of tasks into the dashboard's labelled sections."""
    buckets = defaultdict(list)
    for task in tasks:
        if task.is_pinned and not task.is_complete:
            buckets['pinned'].append(task)
            continue
        buckets[task.due_bucket].append(task)

    return [
        {"key": key, "label": label, "tasks": buckets[key]}
        for key, label in GROUP_LABELS.items()
        if buckets[key]
    ]


def _start_of_today():
    return timezone.localtime(timezone.now()).replace(
        hour=0, minute=0, second=0, microsecond=0,
    )


def dashboard_stats(user):
    """Numbers for the dashboard stat strip and right-hand rail."""
    start_today = _start_of_today()
    end_today = start_today + timedelta(days=1)
    week_ago = timezone.now() - timedelta(days=7)

    tasks = Task.objects.filter(owner=user)
    total = tasks.count()
    completed = tasks.filter(is_complete=True).count()
    pending = total - completed

    return {
        'total': total,
        'pending': pending,
        'completed': completed,
        'overdue': tasks.filter(
            is_complete=False, due_date__lt=timezone.now(),
        ).count(),
        'due_today': tasks.filter(
            is_complete=False, due_date__gte=start_today, due_date__lt=end_today,
        ).count(),
        'completed_week': tasks.filter(
            is_complete=True, completed_at__gte=week_ago,
        ).count(),
        'high_priority': tasks.filter(
            is_complete=False, priority=Task.Priority.HIGH,
        ).count(),
        'completion_rate': round(completed * 100 / total) if total else 0,
        'projects': Project.objects.filter(owner=user, is_archived=False).count(),
    }


def view_counts(user):
    """Small counts shown on the dashboard's smart-view tabs."""
    tasks = Task.objects.filter(owner=user)
    today = timezone.localdate()
    return {
        'all': tasks.filter(is_complete=False).count(),
        'today': tasks.filter(is_complete=False, due_date__date=today).count(),
        'upcoming': tasks.filter(
            is_complete=False, due_date__date__gt=today,
        ).count(),
        'overdue': tasks.filter(
            is_complete=False, due_date__lt=timezone.now(),
        ).count(),
        'someday': tasks.filter(is_complete=False, due_date__isnull=True).count(),
        'completed': tasks.filter(is_complete=True).count(),
    }


def project_progress(user, limit=4):
    """Projects with open work, annotated with totals and progress."""
    projects = (
        Project.objects.filter(owner=user, is_archived=False)
        .annotate(
            total=Count('tasks', distinct=True),
            done=Count('tasks', filter=Q(tasks__is_complete=True), distinct=True),
        )
        .filter(total__gt=0)
        .order_by('-total')[:limit]
    )
    for project in projects:
        project.progress = round(project.done * 100 / project.total) if project.total else 0
    return projects


def completion_streak(user):
    """Consecutive days (ending today or yesterday) with a completed task."""
    completed_days = set(
        Task.objects.filter(
            owner=user,
            is_complete=True,
            completed_at__isnull=False,
        ).values_list('completed_at__date', flat=True)
    )
    if not completed_days:
        return 0

    today = timezone.localdate()
    cursor = today if today in completed_days else today - timedelta(days=1)
    if cursor not in completed_days:
        return 0

    streak = 0
    while cursor in completed_days and streak < 365:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def calendar_month(user, year, month):
    """Build a Sunday-first month grid with tasks attached to each day."""
    first_day = date(year, month, 1)
    weeks_dates = calendar.Calendar(firstweekday=6).monthdatescalendar(year, month)
    range_start = weeks_dates[0][0]
    range_end = weeks_dates[-1][-1]

    tasks = (
        Task.objects.filter(
            owner=user,
            due_date__date__gte=range_start,
            due_date__date__lte=range_end,
        )
        .select_related('project')
        .order_by('due_date')
    )
    by_day = defaultdict(list)
    for task in tasks:
        by_day[timezone.localtime(task.due_date).date()].append(task)

    today = timezone.localdate()
    weeks = []
    for week in weeks_dates:
        cells = []
        for day in week:
            cells.append({
                'date': day,
                'in_month': day.month == month,
                'is_today': day == today,
                'tasks': by_day[day],
            })
        weeks.append(cells)

    previous_month = (first_day - timedelta(days=1)).replace(day=1)
    next_month = (first_day + timedelta(days=32)).replace(day=1)
    return {
        'weeks': weeks,
        'month_label': first_day.strftime('%B %Y'),
        'month_start': first_day,
        'previous': previous_month,
        'next': next_month,
        'weekday_names': ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
    }


def insights_data(user):
    """Two-week activity, streaks and workload breakdowns for Insights."""
    today = timezone.localdate()
    days = [today - timedelta(days=offset) for offset in range(13, -1, -1)]

    completed_tasks = Task.objects.filter(
        owner=user,
        is_complete=True,
        completed_at__isnull=False,
        completed_at__date__gte=days[0],
    ).values_list('completed_at__date', flat=True)
    counts = defaultdict(int)
    for day in completed_tasks:
        counts[day] += 1

    chart = [
        {
            'date': day,
            'label': day.strftime('%a'),
            'day_number': day.day,
            'count': counts[day],
        }
        for day in days
    ]
    max_count = max([row['count'] for row in chart] + [1])
    for row in chart:
        row['height'] = round(row['count'] * 100 / max_count) if row['count'] else 4
        row['is_today'] = row['date'] == today

    best = max(chart, key=lambda row: row['count'])
    total_fortnight = sum(row['count'] for row in chart)

    projects = (
        Project.objects.filter(owner=user, is_archived=False)
        .annotate(
            total=Count('tasks', distinct=True),
            done=Count('tasks', filter=Q(tasks__is_complete=True), distinct=True),
        )
        .order_by('-total')
    )
    for project in projects:
        project.progress = round(project.done * 100 / project.total) if project.total else 0

    pending = Task.objects.filter(owner=user, is_complete=False)
    priority = [
        {
            'key': key,
            'label': label,
            'count': pending.filter(priority=key).count(),
        }
        for key, label in Task.Priority.choices
    ]
    priority_total = sum(row['count'] for row in priority) or 1
    for row in priority:
        row['percent'] = round(row['count'] * 100 / priority_total)

    stats = dashboard_stats(user)
    focus_sessions = FocusSession.objects.filter(
        user=user,
        ended_at__date__gte=days[0],
    )
    focus_minutes = sum(s.duration_minutes for s in focus_sessions)
    return {
        'chart': chart,
        'best_day': best if best['count'] else None,
        'total_fortnight': total_fortnight,
        'daily_average': round(total_fortnight / 14, 1),
        'projects': projects,
        'priority': priority,
        'streak': completion_streak(user),
        'stats': stats,
        'focus_sessions': focus_sessions.count(),
        'focus_minutes': focus_minutes,
    }
