from django.contrib import admin

from .models import Project, Subtask, Task


class SubtaskInline(admin.TabularInline):
    model = Subtask
    extra = 0


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'code', 'color', 'is_archived')
    list_filter = ('color', 'is_archived')
    search_fields = ('name', 'code')


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'owner', 'project', 'due_date', 'priority',
        'is_complete', 'is_pinned',
    )
    list_filter = ('priority', 'is_complete', 'is_pinned', 'project')
    search_fields = ('title', 'description')
    inlines = [SubtaskInline]


@admin.register(Subtask)
class SubtaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'task', 'is_done', 'position')
    list_filter = ('is_done',)
    search_fields = ('title',)
