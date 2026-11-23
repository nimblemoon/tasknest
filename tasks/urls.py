# tasks/urls.py
"""
URL routing for the tasks app.
"""
from django.urls import path

from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('board/', views.board_view, name='board'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('insights/', views.insights_view, name='insights'),
    path('data/', views.data_view, name='data'),
    path('data/export/', views.export_view, name='data_export'),
    path('data/import/', views.import_view, name='data_import'),
    path('filter/', views.filter_tasks_view, name='filter_tasks'),
    path('quick-add/', views.quick_add_view, name='quick_add'),

    path('add/', views.AddTaskView.as_view(), name='add_task'),
    path('tags/', views.tags_view, name='tags'),
    path('tags/new/', views.tag_create_view, name='tag_create'),
    path('tags/<int:pk>/edit/', views.tag_edit_view, name='tag_edit'),
    path('tags/<int:pk>/delete/', views.tag_delete_view, name='tag_delete'),
    path('projects/', views.projects_view, name='projects'),
    path('projects/new/', views.project_create_view, name='project_create'),
    path('projects/<int:pk>/', views.project_detail_view, name='project_detail'),
    path('projects/<int:pk>/edit/', views.project_edit_view, name='project_edit'),
    path('projects/<int:pk>/delete/', views.project_delete_view, name='project_delete'),

    path('<int:pk>/', views.task_detail_view, name='task_detail'),
    path('<int:pk>/comments/add/', views.comment_add_view, name='comment_add'),
    path('<int:pk>/comments/<int:comment_pk>/delete/', views.comment_delete_view, name='comment_delete'),
    path('<int:pk>/edit/', views.EditTaskView.as_view(), name='edit_task'),
    path('<int:pk>/delete/', views.DeleteTaskView.as_view(), name='delete_task'),
    path('<int:pk>/complete/', views.complete_task_view, name='complete_task'),
    path('<int:pk>/pin/', views.toggle_pin_view, name='toggle_pin'),
    path('<int:pk>/subtasks/add/', views.subtask_add_view, name='subtask_add'),
    path(
        '<int:pk>/subtasks/<int:subtask_pk>/toggle/',
        views.subtask_toggle_view,
        name='subtask_toggle',
    ),
    path(
        '<int:pk>/subtasks/<int:subtask_pk>/delete/',
        views.subtask_delete_view,
        name='subtask_delete',
    ),
]
