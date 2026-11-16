#tasks/urls.py
"""
URL routing for the tasks vertical slice.
"""
from django.urls import path

from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('add/', views.AddTaskView.as_view(), name='add_task'),
    path('<int:pk>/edit/', views.EditTaskView.as_view(), name='edit_task'),
    path('<int:pk>/delete/', views.DeleteTaskView.as_view(), name='delete_task'),
    path('<int:pk>/complete/', views.complete_task_view, name='complete_task'),
    path('filter/', views.filter_tasks_view, name='filter_tasks'),
]
