#tasks/views.py
"""
Views for the tasks app: Dashboard, Add/Edit/Delete, Mark Complete, Filter/Sort.

(Objectives O1-O4; Section 6/7.4 of the project spec.)
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, UpdateView

from .forms import TaskFilterForm, TaskForm
from .models import Task
from .utils import apply_task_filters


@login_required
def dashboard_view(request):
    """Home/Dashboard: tasks sorted by nearest deadline/highest priority,
    with overdue tasks flagged, and quick filter controls (O2, O4)."""
    filter_form = TaskFilterForm(request.GET or None)
    status = priority = sort = ''
    if filter_form.is_valid():
        status = filter_form.cleaned_data.get('status', '')
        priority = filter_form.cleaned_data.get('priority', '')
        sort = filter_form.cleaned_data.get('sort', '')

    tasks = apply_task_filters(
        Task.objects.filter(owner=request.user),
        status=status,
        priority=priority,
        sort=sort,
    )

    context = {
        'tasks': tasks,
        'filter_form': filter_form,
        'pending_count': Task.objects.filter(owner=request.user, is_complete=False).count(),
        'completed_count': Task.objects.filter(owner=request.user, is_complete=True).count(),
    }
    return render(request, 'tasks/dashboard.html', context)


class OwnerQuerysetMixin(LoginRequiredMixin):
    """Restrict edit/delete views to tasks owned by the requesting user."""

    def get_queryset(self):
        return Task.objects.filter(owner=self.request.user)


class AddTaskView(LoginRequiredMixin, CreateView):
    """Add Task screen (O1)."""

    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('tasks:dashboard')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, f'Task "{form.instance.title}" was added.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_heading'] = 'Add Task'
        return context


class EditTaskView(OwnerQuerysetMixin, UpdateView):
    """Edit Task screen, reusing the same template as Add Task."""

    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('tasks:dashboard')

    def form_valid(self, form):
        messages.success(self.request, f'Task "{form.instance.title}" was updated.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_heading'] = 'Edit Task'
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
    """Toggle a task's completion state from the dashboard (O3)."""
    task = get_object_or_404(Task, pk=pk, owner=request.user)
    if task.is_complete:
        task.mark_incomplete()
    else:
        task.mark_complete()
    return redirect('tasks:dashboard')


@login_required
def filter_tasks_view(request):
    """Standalone Filter/Sort view (O4), same helper as the dashboard uses."""
    filter_form = TaskFilterForm(request.GET or None)
    status = priority = sort = ''
    if filter_form.is_valid():
        status = filter_form.cleaned_data.get('status', '')
        priority = filter_form.cleaned_data.get('priority', '')
        sort = filter_form.cleaned_data.get('sort', '')

    tasks = apply_task_filters(
        Task.objects.filter(owner=request.user),
        status=status,
        priority=priority,
        sort=sort,
    )
    return render(request, 'tasks/dashboard.html', {
        'tasks': tasks,
        'filter_form': filter_form,
        'pending_count': Task.objects.filter(owner=request.user, is_complete=False).count(),
        'completed_count': Task.objects.filter(owner=request.user, is_complete=True).count(),
    })
