from datetime import timedelta

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.utils import timezone
from django.urls import reverse

from .models import Task


class TaskAccessTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='safe-password')
        self.other_user = User.objects.create_user(username='other', password='safe-password')
        self.task = Task.objects.create(
            owner=self.owner,
            title='Prepare report',
            due_date=timezone.now() + timedelta(days=1),
        )
        self.client.force_login(self.owner)

    def test_dashboard_only_shows_current_users_tasks(self):
        Task.objects.create(
            owner=self.other_user,
            title='Private task',
            due_date=timezone.now() + timedelta(days=2),
        )

        response = self.client.get(reverse('tasks:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Prepare report')
        self.assertNotContains(response, 'Private task')

    def test_complete_endpoint_requires_post(self):
        response = self.client.get(reverse('tasks:complete_task', args=[self.task.pk]))

        self.assertEqual(response.status_code, 405)
        self.task.refresh_from_db()
        self.assertFalse(self.task.is_complete)

    def test_complete_endpoint_toggles_completion_timestamp(self):
        url = reverse('tasks:complete_task', args=[self.task.pk])

        response = self.client.post(url)
        self.task.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.task.is_complete)
        self.assertIsNotNone(self.task.completed_at)

        response = self.client.post(url)
        self.task.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.task.is_complete)
        self.assertIsNone(self.task.completed_at)

    def test_complete_endpoint_enforces_csrf(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.owner)

        response = csrf_client.post(
            reverse('tasks:complete_task', args=[self.task.pk])
        )

        self.assertEqual(response.status_code, 403)
        self.task.refresh_from_db()
        self.assertFalse(self.task.is_complete)

    def test_cannot_toggle_another_users_task(self):
        foreign_task = Task.objects.create(
            owner=self.other_user,
            title='Not yours',
            due_date=timezone.now() + timedelta(days=1),
        )

        response = self.client.post(
            reverse('tasks:complete_task', args=[foreign_task.pk])
        )

        self.assertEqual(response.status_code, 404)
        foreign_task.refresh_from_db()
        self.assertFalse(foreign_task.is_complete)

    def test_task_actions_require_authentication(self):
        client = Client()

        response = client.post(reverse('tasks:complete_task', args=[self.task.pk]))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])
