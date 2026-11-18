# KanMind Backend

REST API backend for the KanMind Kanban frontend, built with Django and
Django REST Framework. Authentication uses DRF token authentication.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

The API is served under `http://127.0.0.1:8000/api/`.

## Environment variables

| Variable          | Default                      | Purpose                       |
|-------------------|------------------------------|-------------------------------|
| `DJANGO_SECRET_KEY` | development key            | Secret key (set in production) |
| `DJANGO_DEBUG`    | `True`                       | Set to `False` in production  |

## Tests and coverage

```powershell
python manage.py test auth_app kanban_app
coverage run --source=auth_app,kanban_app manage.py test auth_app kanban_app
coverage report -m
flake8 --exclude=.venv,*/migrations/* .
```

## Endpoints

| Method | Path                                   | Description                     |
|--------|----------------------------------------|---------------------------------|
| POST   | `/api/registration/`                   | Register a user, returns token  |
| POST   | `/api/login/`                          | Log in, returns token           |
| GET    | `/api/email-check/?email=`             | Look up a user by email         |
| POST   | `/api/email-check/`                    | Same, email as JSON body        |
| GET    | `/api/boards/`                         | Boards the user is a member of  |
| POST   | `/api/boards/`                         | Create a board                  |
| GET    | `/api/boards/{id}/`                    | Board with members and tasks    |
| PATCH  | `/api/boards/{id}/`                    | Update title or members (owner) |
| DELETE | `/api/boards/{id}/`                    | Delete board (owner)            |
| POST   | `/api/tasks/`                          | Create a task on a board        |
| GET    | `/api/tasks/{id}/`                     | Task details                    |
| PATCH  | `/api/tasks/{id}/`                     | Update a task                   |
| DELETE | `/api/tasks/{id}/`                     | Delete a task                   |
| GET    | `/api/tasks/assigned-to-me/`           | Tasks assigned to the user      |
| GET    | `/api/tasks/reviewing/`                | Tasks the user reviews          |
| GET    | `/api/tasks/allcomments/`              | List comments of accessible tasks |
| GET    | `/api/tasks/{id}/comments/`            | List comments of one task (oldest first) |
| POST   | `/api/tasks/{id}/comments/`            | Add a comment to one task (`content` in body) |
| POST   | `/api/tasks/allcomments/`              | Add a comment (`task`, `comment` in body) |
| DELETE | `/api/tasks/{id}/comments/{cid}/`      | Delete own comment              |

Protected endpoints expect the header `Authorization: Token <key>`.
