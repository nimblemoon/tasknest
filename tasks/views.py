# tasks/views.py
"""
Views for the tasks app.

The dashboard is the centre of the product: smart views, grouping by deadline
pressure, and inline actions. Board, calendar and insights are alternate lenses
over the same tasks. Projects and subtasks add lightweight structure.
"""
import csv
import io
import json
from datetime import date, datetime, time, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Max, Q
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, UpdateView

from .forms import (
    CommentForm,
    DashboardFilterForm,
    ProjectForm,
    QuickAddForm,
    SubtaskForm,
    TagForm,
    TaskForm,
)
from .models import FocusSession, Project, Subtask, Tag, Task, TaskComment
from .utils import (
    apply_task_filters,
    base_task_queryset,
    calendar_month,
    dashboard_stats,
    group_tasks,
    insights_data,
    project_progress,
    view_counts,
)


def _safe_next(request, fallback='tasks:dashboard'):
    """Return the posted next URL when it is local, otherwise the fallback."""
    target = request.POST.get('next') or request.GET.get('next')
    if target and url_has_allowed_host_and_scheme(
        target,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return target
    return reverse(fallback)


def _color_choices():
    """Choice metadata for the custom colour picker in project forms."""
    return [
        {
            'value': value,
            'label': label,
            'hex': Project.COLOR_HEX.get(value, '#2F7A5F'),
        }
        for value, label in Project.Color.choices
    ]


def _greeting():
    hour = timezone.localtime().hour
    if hour < 12:
        return 'Good morning'
    if hour < 18:
        return 'Good afternoon'
    return 'Good evening'


def _dashboard_context(request):
    """Shared context builder for the dashboard and the legacy filter URL."""
    filter_form = DashboardFilterForm(request.GET or None, user=request.user)
    data = filter_form.cleaned_data if filter_form.is_valid() else {}

    view = data.get('view') or 'all'
    tasks = apply_task_filters(
        base_task_queryset(request.user),
        view=view,
        priority=data.get('priority', ''),
        project_id=data.get('project').pk if data.get('project') else None,
        tag_id=data.get('tag').pk if data.get('tag') else None,
        q=data.get('q', '').strip(),
        sort=data.get('sort') or 'due',
    )

    params = request.GET.copy()
    params.pop('view', None)
    base_query = params.urlencode()

    return {
        'filter_form': filter_form,
        'active_view': view,
        'groups': group_tasks(tasks),
        'task_count': len(tasks),
        'stats': dashboard_stats(request.user),
        'counts': view_counts(request.user),
        'progress': project_progress(request.user),
        'base_query': base_query,
        'search_query': data.get('q', '').strip(),
        'greeting': _greeting(),
        'today': timezone.localdate(),
        'has_filters': bool(
            data.get('priority') or data.get('project') or data.get('q') or view != 'all'
        ),
    }


@login_required
def dashboard_view(request):
    """Home screen: deadline-first task groups plus workload insights."""
    return render(request, 'tasks/dashboard.html', _dashboard_context(request))


@login_required
def filter_tasks_view(request):
    """Legacy filter URL kept as a redirect into the dashboard."""
    query = request.GET.urlencode()
    url = reverse('tasks:dashboard')
    return redirect(f'{url}?{query}' if query else url)


@login_required
def board_view(request):
    """A kanban-style view grouped by deadline pressure."""
    project_id = request.GET.get('project') or ''
    tasks = base_task_queryset(request.user).filter(is_complete=False)
    if project_id.isdigit():
        tasks = tasks.filter(project_id=project_id)

    buckets = {key: [] for key in ('overdue', 'today', 'tomorrow', 'week', 'later', 'someday')}
    for task in tasks:
        buckets.setdefault(task.due_bucket, []).append(task)

    completed = (
        base_task_queryset(request.user)
        .filter(is_complete=True)
        .order_by('-completed_at')[:15]
    )

    columns = [
        {'key': 'overdue', 'label': 'Overdue', 'tone': 'danger', 'tasks': buckets['overdue']},
        {'key': 'today', 'label': 'Today', 'tone': 'warn', 'tasks': buckets['today']},
        {'key': 'tomorrow', 'label': 'Tomorrow', 'tone': 'brand', 'tasks': buckets['tomorrow']},
        {'key': 'week', 'label': 'This week', 'tone': 'quiet', 'tasks': buckets['week']},
        {'key': 'later', 'label': 'Later', 'tone': 'quiet', 'tasks': buckets['later']},
        {'key': 'someday', 'label': 'No deadline', 'tone': 'quiet', 'tasks': buckets['someday']},
        {'key': 'done', 'label': 'Recently done', 'tone': 'done', 'tasks': list(completed)},
    ]

    return render(request, 'tasks/board.html', {
        'columns': columns,
        'projects': Project.objects.filter(owner=request.user, is_archived=False),
        'active_project': project_id,
        'stats': dashboard_stats(request.user),
        'today': timezone.localdate(),
    })


@login_required
def calendar_view(request):
    """Month calendar with every deadline plotted on its day."""
    today = timezone.localdate()
    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
        if not (1 <= month <= 12 and 2000 <= year <= 2100):
            raise ValueError
    except (TypeError, ValueError):
        year, month = today.year, today.month

    data = calendar_month(request.user, year, month)
    return render(request, 'tasks/calendar.html', {
        **data,
        'stats': dashboard_stats(request.user),
        'today': today,
    })


@login_required
def insights_view(request):
    """Two-week productivity report: activity, streak, projects, priorities."""
    data = insights_data(request.user)
    return render(request, 'tasks/insights.html', {
        **data,
        'today': timezone.localdate(),
    })


@login_required
def task_detail_view(request, pk):
    """Full task page: notes, checklist progress and related work."""
    task = get_object_or_404(
        base_task_queryset(request.user).prefetch_related('subtasks'),
        pk=pk,
    )
    related = (
        base_task_queryset(request.user)
        .filter(project=task.project, is_complete=False)
        .exclude(pk=task.pk)[:4]
        if task.project
        else []
    )
    return render(request, 'tasks/task_detail.html', {
        'task': task,
        'subtask_form': SubtaskForm(),
        'comment_form': CommentForm(),
        'comments': task.comments.select_related('author'),
        'related_tasks': related,
    })


class OwnerQuerysetMixin(LoginRequiredMixin):
    """Restrict edit/delete views to rows owned by the requesting user."""

    def get_queryset(self):
        return Task.objects.filter(owner=self.request.user)


class AddTaskView(LoginRequiredMixin, CreateView):
    """Add Task screen."""

    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('tasks:dashboard')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        due = self.request.GET.get('due')
        if due:
            try:
                parsed = datetime.strptime(due, '%Y-%m-%d').date()
                initial['due_date'] = timezone.make_aware(
                    datetime.combine(parsed, time(hour=17)),
                )
            except ValueError:
                pass
        project = self.request.GET.get('project')
        if project and project.isdigit():
            if Project.objects.filter(owner=self.request.user, pk=project).exists():
                initial['project'] = int(project)
        return initial

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, f'Task "{form.instance.title}" was added.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_heading'] = 'Add task'
        context['form_subtitle'] = (
            'Give it a deadline if it has one. Everything else can wait.'
        )
        context['submit_label'] = 'Create task'
        return context


class EditTaskView(OwnerQuerysetMixin, UpdateView):
    """Edit Task screen, reusing the same template as Add Task."""

    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('tasks:dashboard')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, f'Task "{form.instance.title}" was updated.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_heading'] = 'Edit task'
        context['form_subtitle'] = 'Adjust the details without losing your place.'
        context['submit_label'] = 'Save changes'
        context['task'] = self.object
        return context


class DeleteTaskView(OwnerQuerysetMixin, DeleteView):
    """Delete confirmation screen."""

    model = Task
    template_name = 'tasks/task_confirm_delete.html'
    success_url = reverse_lazy('tasks:dashboard')

    def form_valid(self, form):
        messages.success(self.request, f'Task "{self.object.title}" was deleted.')
        return super().form_valid(form)


@login_required
@require_POST
def complete_task_view(request, pk):
    """Toggle a task's completion state from any screen."""
    task = get_object_or_404(Task, pk=pk, owner=request.user)
    if task.is_complete:
        task.mark_incomplete()
        messages.info(request, f'Reopened "{task.title}".')
    else:
        task.mark_complete()
        messages.success(request, f'Nice — "{task.title}" is done.')
    return HttpResponseRedirect(_safe_next(request))


@login_required
@require_POST
def toggle_pin_view(request, pk):
    task = get_object_or_404(Task, pk=pk, owner=request.user)
    task.is_pinned = not task.is_pinned
    task.save(update_fields=['is_pinned', 'updated_at'])
    return HttpResponseRedirect(_safe_next(request))


@login_required
@require_POST
def quick_add_view(request):
    """Create a task from the global quick-add dialog."""
    form = QuickAddForm(request.POST, user=request.user)
    if form.is_valid():
        task = form.save(commit=False)
        task.owner = request.user
        task.save()
        messages.success(request, f'Added "{task.title}".')
    else:
        first_error = next(iter(form.errors.values()))[0]
        messages.error(request, f'Could not add task: {first_error}')
    return HttpResponseRedirect(_safe_next(request))


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------

@login_required
def projects_view(request):
    projects = (
        Project.objects.filter(owner=request.user)
        .annotate(
            total=Count('tasks', distinct=True),
            done=Count('tasks', filter=Q(tasks__is_complete=True), distinct=True),
        )
        .order_by('is_archived', 'name')
    )
    for project in projects:
        project.progress = (
            round(project.done * 100 / project.total) if project.total else 0
        )

    return render(request, 'projects/index.html', {
        'projects': [p for p in projects if not p.is_archived],
        'archived_projects': [p for p in projects if p.is_archived],
        'form': ProjectForm(user=request.user),
        'color_choices': _color_choices(),
        'stats': dashboard_stats(request.user),
    })


@login_required
def project_create_view(request):
    if request.method != 'POST':
        return redirect('tasks:projects')
    form = ProjectForm(request.POST, user=request.user)
    if form.is_valid():
        project = form.save(commit=False)
        project.owner = request.user
        project.save()
        messages.success(request, f'Project "{project.name}" created.')
        return redirect('tasks:project_detail', pk=project.pk)
    messages.error(request, 'Could not create project. Check the name and try again.')
    return redirect('tasks:projects')


@login_required
def project_detail_view(request, pk):
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    tasks = base_task_queryset(request.user).filter(project=project)
    completed = tasks.filter(is_complete=True).order_by('-completed_at')[:6]
    return render(request, 'projects/detail.html', {
        'project': project,
        'groups': group_tasks(tasks.filter(is_complete=False)),
        'completed_tasks': completed,
        'open_count': tasks.filter(is_complete=False).count(),
        'done_count': tasks.filter(is_complete=True).count(),
        'total_count': tasks.count(),
        'progress': (
            round(tasks.filter(is_complete=True).count() * 100 / tasks.count())
            if tasks.count() else 0
        ),
    })


@login_required
def project_edit_view(request, pk):
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Project updated.')
            return redirect('tasks:project_detail', pk=project.pk)
    else:
        form = ProjectForm(instance=project, user=request.user)
    return render(request, 'projects/form.html', {
        'form': form,
        'project': project,
        'form_heading': 'Edit project',
        'submit_label': 'Save project',
        'color_choices': _color_choices(),
    })


@login_required
def project_delete_view(request, pk):
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    if request.method == 'POST':
        name = project.name
        project.delete()
        messages.success(
            request,
            f'Project "{name}" deleted. Its tasks were kept without a project.',
        )
        return redirect('tasks:projects')
    return render(request, 'projects/confirm_delete.html', {
        'project': project,
        'task_count': project.tasks.count(),
    })


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------

@login_required
def tags_view(request):
    tags = (
        Tag.objects.filter(owner=request.user)
        .annotate(task_count=Count('tasks', distinct=True))
        .order_by('name')
    )
    return render(request, 'tags/index.html', {
        'tags': tags,
        'form': TagForm(user=request.user),
        'color_choices': _color_choices(),
        'stats': dashboard_stats(request.user),
    })


@login_required
def tag_create_view(request):
    if request.method != 'POST':
        return redirect('tasks:tags')
    form = TagForm(request.POST, user=request.user)
    if form.is_valid():
        tag = form.save(commit=False)
        tag.owner = request.user
        tag.save()
        messages.success(request, f'Tag "{tag.name}" created.')
        return redirect('tasks:tags')
    messages.error(request, 'Could not create tag. Check the name and try again.')
    return redirect('tasks:tags')


@login_required
def tag_edit_view(request, pk):
    tag = get_object_or_404(Tag, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = TagForm(request.POST, instance=tag, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tag updated.')
            return redirect('tasks:tags')
    else:
        form = TagForm(instance=tag, user=request.user)
    return render(request, 'tags/form.html', {
        'form': form,
        'tag': tag,
        'form_heading': 'Edit tag',
        'submit_label': 'Save tag',
        'color_choices': _color_choices(),
    })


@login_required
def tag_delete_view(request, pk):
    tag = get_object_or_404(Tag, pk=pk, owner=request.user)
    if request.method == 'POST':
        name = tag.name
        tag.delete()
        messages.success(request, f'Tag "{name}" deleted.')
        return redirect('tasks:tags')
    return render(request, 'tags/confirm_delete.html', {'tag': tag})


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------

@login_required
@require_POST
def comment_add_view(request, pk):
    task = get_object_or_404(Task, pk=pk, owner=request.user)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.task = task
        comment.author = request.user
        comment.save()
        messages.success(request, 'Note added.')
    else:
        messages.error(request, 'Could not add note.')
    return redirect('tasks:task_detail', pk=task.pk)


@login_required
@require_POST
def comment_delete_view(request, pk, comment_pk):
    comment = get_object_or_404(
        TaskComment, pk=comment_pk, task_id=pk, task__owner=request.user,
    )
    task_id = comment.task_id
    comment.delete()
    messages.info(request, 'Note removed.')
    return redirect('tasks:task_detail', pk=task_id)


# ---------------------------------------------------------------------------
# Data export / import
# ---------------------------------------------------------------------------

@login_required
def data_view(request):
    return render(request, 'data/index.html', {
        'stats': dashboard_stats(request.user),
        'task_count': Task.objects.filter(owner=request.user).count(),
        'project_count': Project.objects.filter(owner=request.user).count(),
        'tag_count': Tag.objects.filter(owner=request.user).count(),
    })


@login_required
def export_view(request):
    fmt = request.GET.get('format', 'json').lower()
    if fmt == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="tasknest-tasks.csv"'
        writer = csv.writer(response)
        writer.writerow(['title', 'description', 'due_date', 'priority', 'is_complete', 'is_pinned', 'project', 'tags'])
        for task in base_task_queryset(request.user):
            writer.writerow([
                task.title,
                task.description,
                task.due_date.isoformat() if task.due_date else '',
                task.priority,
                task.is_complete,
                task.is_pinned,
                task.project.name if task.project else '',
                ', '.join(t.name for t in task.tags.all()),
            ])
        return response

    payload = {
        'projects': [
            {'name': p.name, 'code': p.code, 'description': p.description, 'color': p.color, 'is_archived': p.is_archived}
            for p in Project.objects.filter(owner=request.user)
        ],
        'tags': [
            {'name': t.name, 'color': t.color}
            for t in Tag.objects.filter(owner=request.user)
        ],
        'tasks': [],
    }
    for task in base_task_queryset(request.user):
        payload['tasks'].append({
            'title': task.title,
            'description': task.description,
            'due_date': task.due_date.isoformat() if task.due_date else None,
            'priority': task.priority,
            'is_complete': task.is_complete,
            'is_pinned': task.is_pinned,
            'recurrence': task.recurrence,
            'recurrence_interval': task.recurrence_interval,
            'recurrence_end_date': task.recurrence_end_date.isoformat() if task.recurrence_end_date else None,
            'project': task.project.name if task.project else None,
            'tags': [t.name for t in task.tags.all()],
            'subtasks': [{'title': s.title, 'is_done': s.is_done} for s in task.subtasks.all()],
            'comments': [{'body': c.body, 'created_at': c.created_at.isoformat()} for c in task.comments.all()],
        })

    response = HttpResponse(
        json.dumps(payload, indent=2, default=str),
        content_type='application/json',
    )
    response['Content-Disposition'] = 'attachment; filename="tasknest-export.json"'
    return response


@login_required
@require_POST
def import_view(request):
    uploaded = request.FILES.get('file')
    if not uploaded:
        messages.error(request, 'Choose a JSON export file to import.')
        return redirect('tasks:data')
    try:
        raw = uploaded.read().decode('utf-8')
        data = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        messages.error(request, 'That file is not valid JSON.')
        return redirect('tasks:data')

    project_map = {}
    for item in data.get('projects', []):
        project, _ = Project.objects.get_or_create(
            owner=request.user,
            name=item.get('name', 'Imported project'),
            defaults={
                'code': item.get('code', ''),
                'description': item.get('description', ''),
                'color': item.get('color', Project.Color.EMERALD),
                'is_archived': item.get('is_archived', False),
            },
        )
        project_map[project.name] = project

    tag_map = {}
    for item in data.get('tags', []):
        tag, _ = Tag.objects.get_or_create(
            owner=request.user,
            name=item.get('name', 'imported'),
            defaults={'color': item.get('color', Tag.Color.EMERALD)},
        )
        tag_map[tag.name] = tag

    imported = 0
    for item in data.get('tasks', []):
        due_date = None
        if item.get('due_date'):
            try:
                due_date = datetime.fromisoformat(item['due_date'])
                if timezone.is_naive(due_date):
                    due_date = timezone.make_aware(due_date)
            except ValueError:
                due_date = None
        end_date = None
        if item.get('recurrence_end_date'):
            try:
                end_date = date.fromisoformat(item['recurrence_end_date'])
            except ValueError:
                end_date = None

        project = None
        if item.get('project'):
            project = project_map.get(item['project'])
            if project is None:
                project, _ = Project.objects.get_or_create(
                    owner=request.user, name=item['project'],
                )
                project_map[project.name] = project

        task = Task.objects.create(
            owner=request.user,
            project=project,
            title=item.get('title', 'Imported task')[:200],
            description=item.get('description', ''),
            due_date=due_date,
            priority=item.get('priority', Task.Priority.MEDIUM),
            is_complete=item.get('is_complete', False),
            is_pinned=item.get('is_pinned', False),
            recurrence=item.get('recurrence', 'none'),
            recurrence_interval=item.get('recurrence_interval', 1) or 1,
            recurrence_end_date=end_date,
            completed_at=timezone.now() if item.get('is_complete') else None,
        )
        for tag_name in item.get('tags', []):
            tag = tag_map.get(tag_name)
            if tag is None:
                tag, _ = Tag.objects.get_or_create(owner=request.user, name=tag_name)
                tag_map[tag.name] = tag
            task.tags.add(tag)
        for sub in item.get('subtasks', []):
            Subtask.objects.create(
                task=task,
                title=sub.get('title', 'Step')[:200],
                is_done=sub.get('is_done', False),
            )
        for com in item.get('comments', []):
            TaskComment.objects.create(
                task=task,
                author=request.user,
                body=com.get('body', ''),
            )
        imported += 1

    messages.success(request, f'Imported {imported} task{"s" if imported != 1 else ""}.')
    return redirect('tasks:data')


# ---------------------------------------------------------------------------
# Focus sessions
# ---------------------------------------------------------------------------

@login_required
@require_POST
def focus_session_create_view(request):
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        payload = request.POST
    duration = int(payload.get('duration_minutes') or payload.get('duration') or 25)
    if duration < 1:
        duration = 1
    task_id = payload.get('task_id') or payload.get('task')
    task = None
    if task_id:
        task = Task.objects.filter(pk=task_id, owner=request.user).first()
    ended_at = timezone.now()
    started_at = ended_at - timedelta(minutes=duration)
    session = FocusSession.objects.create(
        user=request.user,
        task=task,
        duration_minutes=duration,
        started_at=started_at,
        ended_at=ended_at,
    )
    return JsonResponse({'id': session.pk, 'duration_minutes': session.duration_minutes}, status=201)


# ---------------------------------------------------------------------------
# Subtasks
# ---------------------------------------------------------------------------

@login_required
@require_POST
def subtask_add_view(request, pk):
    task = get_object_or_404(Task, pk=pk, owner=request.user)
    form = SubtaskForm(request.POST)
    if form.is_valid():
        subtask = form.save(commit=False)
        subtask.task = task
        last = task.subtasks.aggregate(max_position=Max('position'))['max_position']
        subtask.position = (last or 0) + 1
        subtask.save()
        messages.success(request, 'Step added.')
    else:
        messages.error(request, 'Add a short step title.')
    return redirect('tasks:task_detail', pk=task.pk)


@login_required
@require_POST
def subtask_toggle_view(request, pk, subtask_pk):
    subtask = get_object_or_404(
        Subtask, pk=subtask_pk, task_id=pk, task__owner=request.user,
    )
    subtask.is_done = not subtask.is_done
    subtask.save(update_fields=['is_done'])
    subtask.task.save(update_fields=['updated_at'])
    return redirect('tasks:task_detail', pk=subtask.task_id)


@login_required
@require_POST
def subtask_delete_view(request, pk, subtask_pk):
    subtask = get_object_or_404(
        Subtask, pk=subtask_pk, task_id=pk, task__owner=request.user,
    )
    task_id = subtask.task_id
    subtask.delete()
    messages.info(request, 'Step removed.')
    return redirect('tasks:task_detail', pk=task_id)
