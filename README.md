# ARIA - Library Room Booking & Face Recognition System

A comprehensive Flask-based application for managing library room bookings with integrated face recognition for access control.

> **Note:** This README covers the entire ARIA project. For detailed Raspberry Pi client setup and usage, see [`aria-app/client/README.md`](aria-app/client/README.md).

## 🚀 Features

- **User Management**: Student, Staff, and Admin roles with role-based access control
- **Room Booking**: Conflict-detected booking system for rooms and events
- **Double-Factor Access**: Choice between **Face Recognition** (FaceNet) and **QR Check-in**
- **Event-Driven Architecture**: Decoupled services communicating via Redis Pub/Sub
- **Docker Compose (local)**: Optional one-command stack for app, simulator, and DB (production VM steps are in **`CLOUD_SETUP.md`**)
- **Access Logging**: Automated entry tracking and email notifications

## 📋 Requirements

- Python 3.8+ (Python 3.12+ supported; `setuptools` is listed in `requirements.txt` for `distutils` compatibility)
- **Database:** **PostgreSQL** is the primary target (e.g. Supabase in production). The stack uses **`psycopg2-binary`** and **`DATABASE_URL`**. MySQL/MariaDB may still work with a suitable SQLAlchemy URL but is no longer the default documented path.
- **Redis:** Used for pub/sub (Pi ↔ cloud), background booking notifications, and **rate limiting in production** (`FLASK_ENV=production` requires `REDIS_URL`).
- Webcam (optional; for local face registration / streaming routes)

## 🛠️ Installation

### Prerequisites

- **PostgreSQL** (local or cloud) for a typical setup, or any DB supported by your `DATABASE_URL`.
- **Redis** for full functionality (booking events + production rate limits).
- Build tools may be needed for some wheels (OpenCV, etc.); on Ubuntu: `build-essential python3-dev`.

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ARIA/aria-app
   ```

2. **Create a virtual environment**
   
   **Linux/macOS:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
   
   **Windows:**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install --upgrade pip setuptools
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   
   Create a `.env` file in the `aria-app/` directory (or export variables). **There are no production-safe defaults for secrets** — see `config.py`.

   ```bash
   # Required for normal local/dev runs
   SECRET_KEY=your-secret-key-here
   DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/ariadb

   # Strongly recommended (required when FLASK_ENV=production)
   REDIS_URL=redis://localhost:6379/0

   # Optional
   FLASK_ENV=development
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   FACE_CONFIDENCE_THRESHOLD=0.85
   SESSION_LIFETIME_MINUTES=480
   MAX_CONTENT_LENGTH=5242880
   ARIA_INSTANCE_DIR=/absolute/path/to/instance   # default: aria-app/instance/
   FLASK_SKIP_BACKGROUND_THREADS=1                 # e.g. for tests / one-off scripts
   ```

   **Production (`FLASK_ENV=production`):** startup requires **`SECRET_KEY`**, **`DATABASE_URL`**, and **`REDIS_URL`**, or the app raises **`RuntimeError`**.

5. **Set up the database**
   - Create a Postgres database (or point `DATABASE_URL` at Supabase / another provider).
   - With `AUTO_CREATE_DB=true` (default), tables are created via `db.create_all()` on startup where appropriate.
   - (Optional) Seed sample data (development only — weak passwords):

     ```bash
     cd aria-app
     python seed.py
     ```

6. **Run the application**
   
   **Direct execution:**
   ```bash
   cd aria-app
   python main.py
   ```
   
   **Or using Flask CLI:**
   
   **Linux/macOS:**
   ```bash
   cd aria-app
   export FLASK_APP=main.py
   export FLASK_ENV=development
   flask run
   ```
   
   **Windows (Command Prompt):**
   ```cmd
   cd aria-app
   set FLASK_APP=main.py
   set FLASK_ENV=development
   flask run
   ```
   
   **Windows (PowerShell):**
   ```powershell
   cd aria-app
   $env:FLASK_APP="main.py"
   $env:FLASK_ENV="development"
   flask run
   ```
   
   The application will be available at `http://127.0.0.1:5000/`

## 📁 Project Structure

```
ARIA/
├── README.md                # This file - project overview
├── CLOUD_SETUP.md           # Supabase, Redis, Linux VM (Caddy, systemd) deploy
├── LICENSE                  # License file
├── aria-app/                # Main application directory
│   ├── main.py              # Application entry point
│   ├── config.py            # Configuration management
│   ├── requirements.txt     # Python dependencies
│   ├── gunicorn.conf.py     # Gunicorn settings (VM / systemd deploys)
│   ├── aria.service         # systemd unit template
│   ├── Caddyfile            # Reverse proxy + TLS (VM deploys)
│   ├── instance/            # Runtime data (gitignored): uploads, faces, .npz
│   ├── website/             # Main Flask application
│   │   ├── __init__.py
│   │   ├── app.py           # Flask app factory
│   │   ├── extensions.py    # Flask-Limiter (shared)
│   │   ├── models/          # SQLAlchemy models
│   │   │   ├── base.py      # Database initialization
│   │   │   ├── user.py      # Student, Staff, Admin models
│   │   │   ├── guest.py     # Ephemeral guest_user (face cleanup)
│   │   │   ├── room.py      # Room and booking models
│   │   │   ├── announcement.py
│   │   │   ├── face.py      # Face recognition models
│   │   │   ├── access.py    # Access log models
│   │   │   ├── feedback.py
│   │   │   └── report.py
│   │   ├── routes/          # Route blueprints
│   │   │   ├── home.py      # Home/dashboard routes
│   │   │   ├── auth.py      # Authentication routes
│   │   │   ├── face.py      # Face recognition routes
│   │   │   ├── announcements.py
│   │   │   ├── rooms.py
│   │   │   ├── bookings.py
│   │   │   ├── views.py     # Legacy views (being refactored)
│   │   │   └── api/         # REST API
│   │   │       ├── __init__.py
│   │   │       └── routes.py
│   │   ├── services/        # Business logic layer
│   │   │   ├── auth_service.py
│   │   │   ├── booking_service.py
│   │   │   ├── face_service.py
│   │   │   ├── scheduler.py # APScheduler (bookings + guest cleanup)
│   │   │   ├── guest_cleanup.py
│   │   │   ├── face_training.py
│   │   │   ├── room_service.py
│   │   │   ├── announcement_service.py
│   │   │   └── mail_service.py
│   │   ├── schemas/         # API schemas
│   │   ├── utils/           # Utility functions
│   │   │   ├── file_utils.py
│   │   │   ├── upload_validation.py  # Image magic-byte + MIME checks
│   │   │   └── validators.py
│   │   ├── static/          # Static assets (CSS, JS, images — not user uploads)
│   │   └── templates/       # Jinja2 templates
│   └── client/              # Edge device client (Raspberry Pi)
│       ├── __init__.py
│       ├── config.py        # Client configuration
│       ├── api_client.py    # API communication
│       ├── face_recognition.py
│       ├── hardware.py      # GPIO/hardware control
│       ├── room_monitor.py  # Booking monitoring
│       ├── main.py          # Main application
│       ├── requirements.txt # Client dependencies
│       └── README.md        # Client-specific documentation
├── docs/                    # Documentation
│   ├── aria_app_context.md  # Technical context and architecture
│   └── ...
└── RaspPiScript/            # Legacy Raspberry Pi scripts
```

## 🔧 Configuration

The application uses environment variables for configuration managed through `config.py`.

### Key Configuration Variables

**Required (no insecure fallbacks in code):**

- `SECRET_KEY` — session signing; **must** be set for any real use. In **`FLASK_ENV=production`**, missing `SECRET_KEY` fails startup.
- `DATABASE_URL` — SQLAlchemy URL (e.g. Postgres). **Required** except in **`testing`**; **required in production**.

**Production (`FLASK_ENV=production`):**

- `REDIS_URL` — **required** (Flask-Limiter storage + Redis pub/sub). Development can omit Redis for the limiter (`memory://` fallback after `DevelopmentConfig.init_app`).
- Session cookies: **`SESSION_COOKIE_SECURE=True`**, **`HTTPONLY`**, **`SameSite=Lax`**, **1 hour** lifetime (see `ProductionConfig` in `config.py`).

**Optional:**

- `FLASK_ENV` / `FLASK_DEBUG`
- `MAIL_*` — SMTP (no credentials in repo)
- `FACE_CONFIDENCE_THRESHOLD` (default `0.85`)
- `SESSION_LIFETIME_MINUTES` — dev session length (production uses 1 hour from config class)
- `MAX_CONTENT_LENGTH` — default **5 MB** (`5242880`)
- `ARIA_INSTANCE_DIR` — override directory for `instance/uploads`, `instance/MalaysianFacesDB`, `.npz` files
- `ARIA_UI_ENABLED`, `ARIA_UI_PHASE` — UI rollout
- `FLASK_SKIP_BACKGROUND_THREADS` — skip APScheduler + Redis subscriber (e.g. tests)
- `AUTO_CREATE_DB` — `db.create_all()` on startup when `true`

Rate limits (Flask-Limiter): default **200/day**, **50/hour** globally; stricter limits on **`/login`** (POST), face registration, and face recognition routes. See `website/extensions.py` and route decorators.

Security headers (non-HSTS) are set in `website/app.py` (`Content-Security-Policy: default-src 'self'`, etc.). **HSTS** should be configured at the reverse proxy (e.g. Caddy) in production.

All options are centralized in `config.py`.

### Frontend Conventions

- Legacy templates remain fallback templates.
- Rebrand templates use `.aria.html` suffix and are selected by UI rollout flags.
- Shared ARIA layout shell is `aria-app/website/templates/base_aria.html`.
- ARIA design tokens and components are in `aria-app/website/static/css/aria-theme.css`.
- **HTMX** is used for server-rendered partial updates, including a modernized toast notification system.
- **DataTables** are used for robust data management with initialization guards to prevent re-initialization conflicts.
- **FullCalendar** is integrated for live booking schedule visualization.

## 🏗️ Architecture

### Design Patterns

- **Application Factory**: Flask app created via factory pattern
- **Service Layer**: Business logic separated from routes
- **Event-Driven**: Decoupled communication via **Redis Pub/Sub**
- **Background workers**: **APScheduler** runs booking checks and hourly **guest face cleanup**; **Redis subscriber** runs in a daemon thread
- **Rate limiting**: **Flask-Limiter** with Redis in production
- **Upload validation**: Face and room image uploads require allowed extension, **`image/jpeg` or `image/png`**, and matching **magic bytes**

### Microservices Architecture

The system is deployed as a suite of Docker containers on a single `aria-network`:

1.  **`flask-app`**: Core web app, API, and the booking scheduler thread.
    - **Development Optimization**: The `static`, `templates`, and `routes` directories are volume-mapped for instant UI/logic updates without container restarts.
2.  **`pi-simulator`**: Mimics the hardware client. Runs face recognition against test images and listens for QR validation events.
3.  **`redis`**: Ephemeral message broker for fast, decoupled event flow.
4.  **`db`**: Database container (often Postgres in newer setups; legacy compose may use MySQL).

### Event Flow (Redis Pub/Sub)

Communication between the web cloud and the edge simulator is strictly event-based:
- **`watch_room:{id}`**: Published by `flask-app` when a booking window opens.
- **`face_matched:{id}`**: Published by `pi-simulator` on successful face identification.
- **`token_validated:{id}`**: Published by `flask-app` after a successful QR check-in; consumed by `pi-simulator` to trigger the door.

### 🛠️ Local Development & Docker

For the most efficient developer experience using Docker:

1. **One-Command Start**: `docker-compose up -d`
2. **Instant UI Updates**: Since `static`, `templates`, and `routes` are bind-mounted, changes to your CSS, JS, HTML, or Python route logic reflect instantly.
   - *Note: If CSS or JS changes don't appear, perform a **Hard Refresh** (Ctrl+Shift+R).*
3. **Database Seeding in Docker**:

   ```bash
   docker exec -it aria-flask-app python seed.py
   ```

## 🔐 Authentication

- Uses Flask-Login for session management
- Passwords hashed with bcrypt
- Role-based access control (Student, Staff, Admin)

## 📡 API Endpoints

The REST API is available at `/api` with Swagger documentation at `/api/docs/`.

### Key Endpoints

- `GET /api/studentlist` - Get all students
- `GET /api/stafflist` - Get all staff
- `GET /api/roomlist` - Get all rooms
- `GET /api/rbooklists` - Get all room bookings
- `POST /api/accesslogs` - Create access log entry
- `GET /api/faces` - Download face database
- `GET /api/facesembeds` - Download face embeddings

## 🤖 Face Recognition

The face recognition system uses:
- **Haar Cascade** for face detection
- **FaceNet** for face embeddings
- **SGD Classifier** for face classification

### Training the Model

1. Register faces through the web interface (`/register_face`)
2. Admin can trigger model training at `/train_data`
3. Training images and **`registered-faces-db*.npz`** files live under **`aria-app/instance/`** (see `FACES_DB_PATH` / `FACES_DB_FILE` in `config.py`), not under `website/static/`

## 🔌 Edge Device Client

The Raspberry Pi client (`aria-app/client/`) provides:
- Room booking monitoring
- Face recognition for access control
- GPIO relay control for door locks
- Automatic access logging

See `client/README.md` for installation and configuration details.

## 🧪 Testing

```bash
cd aria-app
export FLASK_SKIP_BACKGROUND_THREADS=1
pytest
```

`FLASK_SKIP_BACKGROUND_THREADS` avoids starting the APScheduler and Redis subscriber during tests. Pytest uses **`create_app('testing')`**, which sets an in-memory SQLite DB and a test `SECRET_KEY` (see `tests/conftest.py`).

```bash
pytest --cov=website
```

## ☁️ Production & cloud

For **Supabase + Redis + Linux VM** (systemd, Caddy, Gunicorn, env file, guest migration SQL), see **[`CLOUD_SETUP.md`](CLOUD_SETUP.md)**. Templates: `aria-app/gunicorn.conf.py`, `aria-app/aria.service`, `aria-app/Caddyfile`.

## 📝 Development

### Code Style

- Follow PEP 8
- Use type hints where possible
- Document functions and classes

### Adding New Features

1. Create model in `website/models/`
2. Create service in `website/services/`
3. Create routes in `website/routes/`
4. Update templates if needed

## 🐛 Known Issues

- Face recognition requires local camera access
- Database migrations not yet implemented (using existing schema)

## 🔧 Troubleshooting

### Database connection

Verify **`DATABASE_URL`** matches your provider (Postgres URI, pooler port for Supabase, etc.). The app does not fall back to a local MySQL URL.

### Python 3.12+ Issues

**Error: `ModuleNotFoundError: No module named 'distutils'`**

Python 3.12+ removed `distutils` from the standard library. The `requirements.txt` includes `setuptools` which provides `distutils` compatibility. If you encounter this error:

1. Ensure `setuptools` is installed:
   ```bash
   pip install --upgrade setuptools
   ```

2. If the error persists, install it before other packages:
   ```bash
   pip install setuptools wheel
   pip install -r requirements.txt
   ```

### Virtual Environment Activation Issues

**Linux/macOS:** If `source venv/bin/activate` doesn't work, try:
```bash
. venv/bin/activate
```

**Windows:** If activation fails, ensure you're using the correct path:
- Command Prompt: `venv\Scripts\activate.bat`
- PowerShell: `venv\Scripts\Activate.ps1` (may require execution policy change)

## 🚀 CI/CD Pipeline

The project uses GitHub Actions for Continuous Integration and Continuous Deployment (CI/CD). The pipeline is defined in `.github/workflows/ci-cd.yml`.

### Pipeline Stages
1. **Lint**: Code style (`ruff`) and security (`bandit`) checks.
2. **Test**: Unit tests run via `pytest` with a live MySQL and Redis service containers.
3. **Docker Build**: Validates `flask-app` and `pi-simulator` container builds.

## 🔄 Refactoring Status

This codebase has been comprehensively refactored:

✅ **Completed:**
- Service layer refactor and blueprint-based routing
- Configuration management (`config.py`)
- QR Check-in system (Service, Routes, Mail Integration)
- Core API (Flask-RESTX)
- Face recognition service (FaceNet/SGD)
- Dockerization (Compose, Dockerfiles, Unified Config)
- Redis Event Flow (Pub/Sub, Background Scheduler)
- Pi Simulator (Event-driven, static image loop)

🔄 **In Progress:**
- Migration of remaining legacy `views.py` routes

📋 **Planned:**
- Alembic database migrations

## 📄 License

See LICENSE file for details.

## 👥 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📧 Support

For issues and questions, please open an issue on the repository.

---

**Note**: This is a refactored version of the original ARIA system. The refactoring focused on:
- Removing hard-coded secrets and paths
- Improving code organization
- Adding proper configuration management
- Separating concerns (models, services, routes)
- Making the codebase more maintainable and testable
