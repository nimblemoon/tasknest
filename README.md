# TaskNest

TaskNest is a calm, deadline-first task manager built for students. It turns a
plain to-do list into a small workspace: projects, checklists, deadline
pressure views, a calendar, a board, focus sessions, and two-week insights.

## Features

- **Tasks** — title, notes, due date (optional), priority (low/medium/high),
  pinning, and completion with timestamps.
- **Projects** — colour-coded containers with code labels, archive support,
  and automatic progress tracking.
- **Subtasks** — checklist steps inside a task with a progress bar.
- **Smart views** — All, Today, Upcoming, Overdue, No date, and Done, plus
  search, project/priority filters, and four sort orders.
- **Board** — seven columns grouped by deadline pressure, with quick
  complete/edit/delete.
- **Calendar** — month grid with every deadline plotted on its day; click a
  day to add a task dated for it.
- **Insights** — 14-day completion chart, streak, completion rate, priority
  mix, and per-project progress.
- **Focus timer** — a 25/5 Pomodoro widget with a gentle chime.
- **Accounts** — registration, login, profile with avatar (max 2 MB) and
  stats, settings (dark mode, email notifications, timezone), and password
  change.
- **Design** — responsive app shell with sidebar, top bar, global search,
  quick-add dialog, keyboard shortcuts (`n`, `/`, `g d/b/c/i`), and a
  light/dark theme that follows the account.

## Tech stack

- Python 3.13, Django 5.2
- SQLite by default (PostgreSQL via `DATABASE_URL`)
- Pillow for avatar handling
- Vanilla CSS design system + a small JavaScript module (no build step)

## Getting started

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env          # set SECRET_KEY, DEBUG, DATABASE_URL
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Then open http://127.0.0.1:8000/ and create an account.

## Environment variables

| Variable       | Description                                    |
| -------------- | ---------------------------------------------- |
| `SECRET_KEY`   | Django secret key (required)                   |
| `DEBUG`        | `True`/`False` (default `False`)               |
| `DATABASE_URL` | PostgreSQL URL; empty uses local SQLite         |
| `ALLOWED_HOSTS`| Comma-separated hosts when `DEBUG=False`       |

## Project structure

```
accounts/   auth, profile, settings, profile signals
tasks/      tasks, projects, subtasks, views, utils, forms
tasknest/   project settings, urls, middleware, context processors
templates/  base shell, partials, account/task/project templates
static/     design system CSS, app JavaScript
```

## Keyboard shortcuts

| Key         | Action                  |
| ----------- | ----------------------- |
| `n`         | Quick add a task        |
| `/`         | Focus global search     |
| `g` then `d`| Dashboard               |
| `g` then `b`| Board                   |
| `g` then `c`| Calendar                |
| `g` then `i`| Insights                |
| `Esc`       | Close dialogs/sidebar   |

## Tests

```bash
DATABASE_URL=sqlite:///db.sqlite3 python manage.py test
```

22 tests cover task access control, completion toggling, avatar validation,
timezone middleware, model behaviour, project/subtask ownership, and screen
smoke tests.

## License

Educational project — TaskNest, Final Project Development Session.
