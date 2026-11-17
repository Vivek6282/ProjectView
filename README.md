# ProjectView

ProjectView is a production-grade Django 5 project-deadline tracker featuring role-based access control (Employee, Manager, HR Manager), an executive analytics dashboard with Chart.js, and a secure real-time polling chat system.

The application is configured to run locally on SQLite or in production on Render with Gunicorn, WhiteNoise, and a MySQL-compatible database (such as TiDB Serverless).

---

## Key Features

### 1. Role-Based Access Control (RBAC) & Workflow Permissions
User permissions are determined by the `UserProfile.role` field:
- **Employee (`employee`)**: Access to assigned projects, interactive onboarding flow, participation in team chat rooms, direct messaging, and personal broadcast acknowledgment. Assigned employees (or the project creator) can submit deliverables and mark projects complete.
- **Manager (`manager`)**: Project creation, team member assignment, workflow management, team deadline tracking, analytics dashboard, creating group chat rooms, marking projects complete, uploading/deleting project deliverables, and participating in management discussions.
- **HR Manager (`hr_manager`)**: Organizational visibility, access to the restricted HR-Management Bridge chat room, project workflow permissions, team member assignment, company-wide broadcasts, and HR administrative controls.
- **Staff / Admin (`is_staff=True`)**: Full administrative access, project CRUD operations, user management, and company-wide broadcast authoring.

#### Project Workflow & Deliverable Permissions
- **Mark Project Complete (`submit_project_complete`)**: Restricted to Managers, HR, Staff/Superuser, the Project Creator, or assigned team members.
- **Upload Deliverables (`upload_project_asset`)**: Restricted to Managers, HR, Staff/Superuser, the Project Creator, or assigned team members. Blocked once a project is marked `Done`.
- **Delete Deliverables (`delete_project_asset`)**: Restricted to the asset uploader, the project creator, or Manager/HR/Staff.
- **Secure File Downloads (`download_project_asset`)**: Login-protected endpoint (`/projects/asset/<id>/download/`) enforcing `X-Content-Type-Options: nosniff`, RFC-safe filename encoding, inline display for safe images, and attachment download for other files. Missing files on disk trigger user-facing notifications instead of unhandled 500 server crashes.

### 2. Team Chat & Messaging
- **Public & System Rooms**:
  - `General`: System-wide public room accessible by all team members.
  - `HR-Management Bridge`: Private system room automatically created for Managers and HR Managers.
  - *Note*: System rooms are protected against deletion.
- **Group Chats & Direct Messages**: Users can create ad-hoc group channels or initiate 1-on-1 direct conversations.
- **Secure File Attachments**:
  - Served via authenticated view (`/chat/attachment/<id>/`) enforcing room membership and `X-Content-Type-Options: nosniff`.
  - Strict upload validation: file extension allowlist (images, PDFs, documents, audio, zip/tar archives) and a 10 MB file size limit. SVG files are barred from inline rendering to mitigate script injection risks.
- **Broadcasts & Announcements**: Staff and HR can broadcast high-priority messages requiring explicit user acknowledgment.
- **Interactive UI**: Threaded replies, user mentions (`@username`), emoji reactions, unread counters, and search.

### 3. Analytics Dashboard
- Project timeline and deadline trackers with urgency indicators.
- Interactive Chart.js visualizations for project health, completion rates, and workload distribution.

---

## Architecture & Technology Stack

- **Framework**: Django 5.x (Python 3.12+)
- **WSGI & Static Files**: Gunicorn with WhiteNoise (`CompressedManifestStaticFilesStorage` in production, `StaticFilesStorage` in development)
- **Database**: SQLite for local development; MySQL/TiDB via `dj-database-url` and `PyMySQL` in production
- **Frontend**: Bootstrap 5.3, Bootstrap Icons, Chart.js, Vanilla JavaScript

---

## Environment Variables

Configure the following variables in `.env` (refer to `.env.example`):

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | Production: Yes, Local: No | Insecure dev key (DEBUG only) | Django secret key. When `DEBUG=False`, startup will fail if this is unset or set to the fallback. |
| `DEBUG` | No | `False` | Set to `True` for local development. Set to `False` in production. |
| `DATABASE_URL` | No | `sqlite:///db.sqlite3` | Database connection URL. Supports MySQL/TiDB (e.g. `mysql://user:pass@host:4000/db?ssl={"ca":"/etc/ssl/certs/ca-certificates.crt"}`) or PostgreSQL. |
| `ALLOWED_HOSTS` | Production: Yes | `localhost,127.0.0.1` | Comma-separated list of allowed hostnames. In Render environments, `RENDER_EXTERNAL_HOSTNAME` is automatically appended. |
| `CSRF_TRUSTED_ORIGINS` | No | Derived from `ALLOWED_HOSTS` | Comma-separated list of trusted origins for CSRF (e.g., `https://projectview.onrender.com`). |
| `RENDER_EXTERNAL_HOSTNAME` | No | `""` | Render environment variable containing the public URL for the service. |
| `MEDIA_ROOT` | No | `<BASE_DIR>/media` | Absolute or relative path to store user-uploaded chat attachments. In Render, point this to your persistent disk mount path. |

---

## Quick Start (Local Development)

### Prerequisites
- Python 3.12+
- `pip` or `uv`

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/Vivek6282/ProjectView.git
cd ProjectView

# Using standard venv
python -m venv .venv
# On Windows:
.\.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment
Create a local `.env` file:
```ini
DEBUG=True
SECRET_KEY=local-dev-insecure-secret-key-32-chars-long
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 3. Apply Migrations & Seed Data
```bash
python manage.py migrate
python manage.py seed_data
```

### 4. Run Development Server
```bash
python manage.py runserver
```
Navigate to `http://127.0.0.1:8000/`.

---

## Default Seed Credentials (Local Development Only)

> [!WARNING]
> The default credentials seeded by `seed_data` are strictly for local testing and demonstration. **Never use these credentials or run `seed_data` with default passwords in a production environment.**

| Username | Default Password | Role | Description |
|---|---|---|---|
| `admin` | `admin123` | Staff / Admin | Full access to dashboard, project CRUD, user management |
| `manager1` | `manager123` | Manager | Project tracking, analytics dashboard, team chats |
| `hr1` | `hr123` | HR Manager | HR-Management Bridge room, broadcasts, employee visibility |
| `user1` | `user123` | Employee | Assigned projects, onboarding walkthrough, team chats |
| `user2` | `user123` | Employee | Read-only projects, team chats |

---

## Running Tests & Checks

Execute the test suite:
```bash
python manage.py test accounts chat
```

Verify migration status:
```bash
python manage.py makemigrations --check
```

Validate production deployment settings:
```bash
# Set production environment variables
export DEBUG=False
export SECRET_KEY="a-secure-production-random-secret-key-goes-here"
export ALLOWED_HOSTS="example.com"
export RENDER_EXTERNAL_HOSTNAME="example.com"

python manage.py check --deploy
```

---

## Deployment to Render

This project is configured for deployment as a Render Web Service via `render.yaml` and `build.sh`.

### 1. Build Process (`build.sh`)
During build, Render executes:
```bash
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
```

### 2. Persistent Disk Configuration (Media Uploads)
Because Render's container filesystem is ephemeral and reset across deploys, configure a **Persistent Disk** for chat attachments:
1. In the Render Dashboard, attach a Disk (e.g., size 1 GB, mounted at `/var/data`).
2. Add an environment variable in your service:
   - `MEDIA_ROOT=/var/data/media`
3. Attachments uploaded by users will now persist safely across deploys and container restarts.
