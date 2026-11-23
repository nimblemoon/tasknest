from datetime import timedelta

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.utils import timezone
from django.urls import reverse

from .models import Project, Subtask, Task


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


class TaskModelTests(TestCase):
    def test_task_without_deadline_is_not_overdue(self):
        task = Task.objects.create(
            owner=User.objects.create_user(username='alice', password='safe-password'),
            title='Someday task',
            due_date=None,
        )

        self.assertFalse(task.is_overdue)
        self.assertEqual(task.humanized_due, 'No deadline')
        self.assertEqual(task.due_bucket, 'someday')

    def test_pinned_task_stays_at_top_of_dashboard(self):
        user = User.objects.create_user(username='pinner', password='safe-password')
        Task.objects.create(owner=user, title='Plain', due_date=timezone.now() + timedelta(days=2))
        pinned = Task.objects.create(
            owner=user, title='Pinned', due_date=timezone.now() + timedelta(days=5), is_pinned=True,
        )
        self.client = Client()
        self.client.force_login(user)
        response = self.client.get(reverse('tasks:dashboard'))
        self.assertContains(response, 'Pinned')


class ProjectAccessTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='owner2', password='safe-password')
        self.other = User.objects.create_user(username='other2', password='safe-password')
        self.project = Project.objects.create(owner=self.owner, name='Capstone', color='coral')

    def test_owner_can_open_project_detail(self):
        client = Client()
        client.force_login(self.owner)
        response = client.get(reverse('tasks:project_detail', args=[self.project.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Capstone')

    def test_foreign_user_gets_404(self):
        client = Client()
        client.force_login(self.other)
        response = client.get(reverse('tasks:project_detail', args=[self.project.pk]))
        self.assertEqual(response.status_code, 404)

    def test_project_progress_counts_tasks(self):
        Task.objects.create(owner=self.owner, project=self.project, title='A', due_date=timezone.now())
        Task.objects.create(owner=self.owner, project=self.project, title='B', due_date=timezone.now(), is_complete=True,
                            completed_at=timezone.now())
        self.assertEqual(self.project.total_tasks, 2)
        self.assertEqual(self.project.done_tasks, 1)
        self.assertEqual(self.project.progress_percent, 50)


class SubtaskAccessTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='subowner', password='safe-password')
        self.other = User.objects.create_user(username='subother', password='safe-password')
        self.task = Task.objects.create(owner=self.owner, title='Parent', due_date=timezone.now())
        self.subtask = Subtask.objects.create(task=self.task, title='Step one')

    def test_owner_can_toggle_subtask(self):
        client = Client()
        client.force_login(self.owner)
        response = client.post(reverse('tasks:subtask_toggle', args=[self.task.pk, self.subtask.pk]))
        self.assertEqual(response.status_code, 302)
        self.subtask.refresh_from_db()
        self.assertTrue(self.subtask.is_done)

    def test_foreign_user_cannot_toggle_subtask(self):
        client = Client()
        client.force_login(self.other)
        response = client.post(reverse('tasks:subtask_toggle', args=[self.task.pk, self.subtask.pk]))
        self.assertEqual(response.status_code, 404)
        self.subtask.refresh_from_db()
        self.assertFalse(self.subtask.is_done)


class ScreenSmokeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='smoke', password='safe-password')
        self.client = Client()
        self.client.force_login(self.user)

    def test_all_main_screens_load(self):
        for url_name in ('tasks:dashboard', 'tasks:board', 'tasks:calendar', 'tasks:insights',
                         'tasks:projects', 'accounts:profile', 'accounts:settings'):
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 200, url_name)

    def test_quick_add_creates_task(self):
        response = self.client.get(reverse('tasks:dashboard'))
        csrf = None
        import re
        match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', response.content.decode())
        self.assertIsNotNone(match)
        csrf = match.group(1)
        response = self.client.post(
            reverse('tasks:quick_add'),
            {'title': 'Quick smoke task', 'priority': 'medium', 'csrfmiddlewaretoken': csrf},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Task.objects.filter(owner=self.user, title='Quick smoke task').exists())

    def test_new_screens_load(self):
        task = Task.objects.create(owner=self.user, title='Detail task', due_date=timezone.now())
        for url_name in ('tasks:tags', 'tasks:data'):
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 200, url_name)
        response = self.client.get(reverse('tasks:task_detail', args=[task.pk]))
        self.assertEqual(response.status_code, 200)

    def test_focus_session_endpoint_creates_session(self):
        response = self.client.post(
            reverse('tasks:focus_session_create'),
            data='{"duration_minutes": 25}',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['duration_minutes'], 25)
