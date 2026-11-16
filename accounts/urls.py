"""
URL routing for the accounts vertical slice.
"""
from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.TaskNestLoginView.as_view(), name='login'),
    path('logout/', views.TaskNestLogoutView.as_view(), name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('settings/', views.settings_view, name='settings'),
    path('settings/password/', views.change_password_view, name='change_password'),
]