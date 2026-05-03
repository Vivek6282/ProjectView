# Project View

Premium Django project-deadline tracker with role-based access, admin dashboard with Chart.js analytics, and editorial UI.

## Quick Start

```bash
# Install
pip install -r requirements.txt

# Database
python manage.py migrate

# Seed data
python manage.py seed_data

# Run
python manage.py runserver
```

## Credentials

| User | Password | Role |
|------|----------|------|
| admin | admin123 | Admin (dashboard + CRUD + user mgmt) |
| user1 | user123 | User (read-only projects) |
| user2 | user123 | User (read-only projects) |

## URLs

| Route | Access | Purpose |
|-------|--------|---------|
| `/login/` | Public | Login |
| `/logout/` | Auth | Logout |
| `/intro/` | Users | Post-login welcome page |
| `/projects/` | Users | Project list (search, filter, sort) |
| `/projects/<id>/` | Users | Project detail |
| `/dashboard/` | Admin | Analytics overview + charts |
| `/dashboard/projects/` | Admin | Manage projects (CRUD) |
| `/dashboard/projects/create/` | Admin | Create project |
| `/dashboard/projects/<id>/edit/` | Admin | Edit project |
| `/dashboard/projects/<id>/delete/` | Admin | Delete project |
| `/dashboard/users/` | Admin | User list |
| `/dashboard/users/create/` | Admin | Create new user |

## Permission Model

- **Admin** (`is_staff=True`): Full access to dashboard, project CRUD, user management
- **Users**: Read-only access to `/intro/`, `/projects/`, `/projects/<id>/`
- **No public signup** — only admins can create users
- All protected views enforce server-side permissions via `@staff_member_required` or `@login_required`

## Stack

- Django 5.x with SQLite (swap-ready for Postgres)
- Bootstrap 5.3 + Bootstrap Icons (CDN)
- Chart.js (CDN)
- Vanilla JS with IntersectionObserver scroll animations
- `prefers-reduced-motion` respected
