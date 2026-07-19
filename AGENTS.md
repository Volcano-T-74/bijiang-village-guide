# AGENTS.md

## Project Overview

This workspace contains a Django backend/admin project with a separate Vue frontend.

- Backend: Django 5.2.16
- Admin UI: django-simpleui 2026.1.13
- Frontend: Vue 3 + Vite
- Database: SQLite, stored in `db.sqlite3`
- Backend app: `main`
- Django project package: `config`
- Vue project directory: `frontend`

## Working Directory

Run backend commands from the repository root, the directory that contains `manage.py`:

```powershell
.
```

Run frontend commands from:

```powershell
.\frontend
```

## Backend Setup

Use the existing Python virtual environment:

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
.\.venv\Scripts\Activate.ps1
```

Install backend dependencies if needed:

```powershell
python -m pip install -r requirements.txt
```

Run Django checks:

```powershell
python manage.py check
```

Apply migrations:

```powershell
python manage.py migrate
```

Start the Django development server:

```powershell
python manage.py runserver 127.0.0.1:8000
```

Backend/admin URL:

```text
http://127.0.0.1:8000/admin/
```

## Frontend Setup

The frontend is a separate Vue 3 + Vite project in `frontend/`.

Install frontend dependencies:

```powershell
pnpm install
```

Start the Vue development server:

```powershell
pnpm dev --host 127.0.0.1
```

Build the frontend:

```powershell
pnpm build
```

Frontend URL:

```text
http://127.0.0.1:5173/
```

## Current Conventions

- Keep Django backend code under `config/` and `main/`.
- Keep Vue frontend code under `frontend/src/`.
- Keep Django admin available at `/admin/`.
- Do not replace SimpleUI unless explicitly requested.
- Keep `LANGUAGE_CODE = "zh-hans"` and `TIME_ZONE = "Asia/Shanghai"` unless the user asks otherwise.
- Add Python dependencies to `requirements.txt`.
- Add frontend dependencies through `frontend/package.json`.

## Verification Checklist

Before reporting backend changes as complete, run:

```powershell
python manage.py check
python manage.py test
```

Before reporting frontend changes as complete, run:

```powershell
pnpm build
```

When changing server behavior, verify the relevant local URL with an HTTP request or browser check.

## Notes For Future Agents

- The user prefers direct execution once the task is clear.
- Preserve existing project structure and avoid broad refactors.
- Do not delete `db.sqlite3` or the `.venv` directory unless the user explicitly requests it.
- The Django superuser previously created is `bijiangcun`.
- Treat Vue as the frontend website and Django as the backend/admin service.
