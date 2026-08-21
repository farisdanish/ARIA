# ARIA (Automated Room Identification & Access)

ARIA is an integrated library room booking and smart access control system. The platform combines a modernized server-rendered web application, a secure Flask-RESTX device API, Redis-backed pub/sub workflows, FaceNet biometric verification, a public guest demo experience, and an edge device client (or simulator) for automated door access.

This README covers the core web application and platform services. For edge client setup and hardware details, see [`aria-app/client/README.md`](file:///home/nian014/projects/ARIA/aria-app/client/README.md).

---

## What The System Currently Does

- **Role-Based Accounts & Dashboards**: Dedicated portal views and authorization for Students, Staff, and Administrators.
- **Modernized Responsive Interface**: Built with Tailwind CSS, Alpine.js, and HTMX partials for seamless reactivity, alongside FullCalendar for scheduling.
- **Room & Event Bookings**: Conflict-free booking creation with PostgreSQL advisory locking to prevent race conditions and cross-type double-booking.
- **Secure QR Check-In**: Cryptographically signed, single-use QR tokens bound to booking owners with replay protection and automatic door-unlock triggering.
- **Biometric Face Recognition**: Pipeline utilizing OpenCV, Keras FaceNet (160×160 embeddings), and an SGD classifier with thread-safe model reloading.
- **Public Guest Face Demo (`/demo`)**: Live camera face enrollment, cosine-similarity verification, session lifecycle management, and visitor audit logs.
- **Edge Device Integration**: Bearer-authenticated REST API and Redis pub/sub synchronization (`watch_room`, `face_matched`, `token_validated`) for Raspberry Pi hardware or simulator.
- **Database Migrations**: Version-controlled database schema management via Flask-Migrate (Alembic) with automated baseline auto-stamping in CI/CD.
- **Automated Background Jobs**: APScheduler tasks for upcoming booking notifications and hourly guest demo face data purges.
- **Containerized Stack**: Local Docker Compose environment with PostgreSQL 15, Redis 7, Flask app, and the Pi simulator.

---

## Repository Layout

```text
ARIA/
├── README.md
├── docker-compose.yml
├── render.yaml
├── .github/
│   └── workflows/
│       ├── ci-cd.yml
│       └── deploy.yml
├── supabase/
│   └── rls_lockdown.sql
├── pi-simulator/
│   └── test_images/
├── RaspPiScript/
└── aria-app/
    ├── main.py
    ├── config.py
    ├── seed.py
    ├── requirements.txt
    ├── gunicorn.conf.py
    ├── aria.service
    ├── Caddyfile
    ├── Dockerfile
    ├── migrations/
    │   ├── alembic.ini
    │   ├── env.py
    │   └── versions/
    ├── client/
    │   ├── main.py
    │   ├── simulator_main.py
    │   ├── api_client.py
    │   ├── face_recognition.py
    │   ├── hardware.py
    │   ├── room_monitor.py
    │   └── Dockerfile.simulator
    ├── tests/
    │   ├── conftest.py
    │   ├── test_security.py
    │   ├── test_ui_rollout.py
    │   ├── unit/
    │   ├── integration/
    │   └── e2e/
    └── website/
        ├── app.py
        ├── extensions.py
        ├── models/
        ├── routes/
        │   ├── api/
        │   ├── auth.py
        │   ├── bookings.py
        │   ├── rooms.py
        │   ├── announcements.py
        │   ├── face.py
        │   ├── demo.py
        │   └── home.py
        ├── services/
        ├── schemas/
        ├── static/
        ├── templates/
        └── utils/
```

### Key Directories
- **`aria-app/website/`**: Application factory, blueprints, SQLAlchemy models, services, templates, and static assets.
- **`aria-app/client/`**: Raspberry Pi edge client and simulator daemon.
- **`aria-app/migrations/`**: Alembic database migration scripts managed by Flask-Migrate.
- **`aria-app/tests/`**: Unit, integration, security, and Playwright E2E test suites.
- **`supabase/`**: Supabase Row Level Security (RLS) hardening scripts.
- **`pi-simulator/`**: Test images and fixtures for containerized simulation.

---

## Runtime Architecture

```
                  ┌──────────────────────────────────────────────┐
                  │                 Browser Client               │
                  │   (Tailwind CSS + Alpine.js + HTMX / /demo)  │
                  └──────────────────────┬───────────────────────┘
                                         │ HTTPS / Session Cookie
                                         ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        ARIA Flask Application                          │
│                                                                        │
│  ┌───────────────────────┐   ┌──────────────────────────────────────┐  │
│  │ Web Blueprints        │   │ Flask-RESTX Device API               │  │
│  │ (Auth, Rooms, Bookings│   │ (Bearer Token Auth via               │  │
│  │  Announcements, Demo) │   │  DEVICE_API_TOKEN)                   │  │
│  └──────────┬────────────┘   └──────────────────┬───────────────────┘  │
│             │                                   │                      │
│             ▼                                   ▼                      │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Services Layer (Booking, Face, QR, Demo, Room, Mail, Scheduler)  │  │
│  └──────────────────┬───────────────────────────┬───────────────────┘  │
└─────────────────────┼───────────────────────────┼──────────────────────┘
                      │                           │
         SQLAlchemy   ▼              Redis Pub/Sub▼
   ┌───────────────────────┐         ┌────────────────────────┐
   │ PostgreSQL Database   │         │ Redis 7 Instance       │
   │ (Flask-Migrate/RLS)   │         │ (Pub/Sub & Rate Limits)│
   └───────────────────────┘         └───────────┬────────────┘
                                                 │
                                                 │ Event Channels
                                                 ▼
                                     ┌────────────────────────┐
                                     │ Raspberry Pi / Edge    │
                                     │ (Client or Simulator)  │
                                     └────────────────────────┘
```

### Redis Event Channels
- **`watch_room:{room_id}`**: Published by the Flask scheduler when an approved booking is within the lead time window.
- **`face_matched:{room_id}`**: Published by the edge device upon successful biometric match to mark bookings ongoing and log access.
- **`token_validated:{room_id}`**: Published by Flask after successful QR check-in to trigger door unlock on the edge device.

---

## Requirements

- **Python 3.8+**
- **PostgreSQL 14+** (configured via `DATABASE_URL`)
- **Redis 6+** (required for pub/sub, background threads, and production rate limiting)
- **C/C++ Build Tools & CMake** (for dlib/OpenCV dependencies if installing outside Docker)
- **Webcam / Video Device** (optional, for live client-side face capture)

---

## Local Setup

### 1. Clone and Install Dependencies

```bash
git clone <repository-url>
cd ARIA/aria-app
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create an environment file or export variables:

```bash
# Core Configuration
export FLASK_ENV=development
export SECRET_KEY=dev-secret-key-change-in-production
export DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/ariadb
export REDIS_URL=redis://localhost:6379/0
export DEVICE_API_TOKEN=dev-device-token-12345

# Optional Settings
export SESSION_LIFETIME_MINUTES=60
export FACE_CONFIDENCE_THRESHOLD=0.85
export ARIA_UI_ENABLED=true
export ARIA_UI_PHASE=all
export AUTO_CREATE_DB=false
```

### 3. Initialize Database Migrations

Apply the database migrations to set up the database schema:

```bash
flask db upgrade
```

*(Optional)* Seed sample rooms, accounts, and demo data:

```bash
python seed.py
```

### 4. Run the Development Server

```bash
python main.py
```

The application will be accessible at `http://localhost:5000`.

---

## Docker Compose (Recommended for Local Dev)

The root [`docker-compose.yml`](file:///home/nian014/projects/ARIA/docker-compose.yml) provisions the complete stack:

- **`db`**: PostgreSQL 15 database
- **`redis`**: Redis 7 service
- **`flask-app`**: ARIA web server running with live-reloading mounts
- **`pi-simulator`**: Automated edge client simulating camera feeds and door access

Run the stack:

```bash
docker-compose up --build
```

---

## Database Management & Migrations

Database schema changes are managed via **Flask-Migrate (Alembic)**:

```bash
# Apply pending migrations
flask db upgrade

# Generate a new migration after modifying models
flask db migrate -m "describe schema change"

# View current migration revision
flask db current
```

> **Note for Production:** In production (`FLASK_ENV=production`), `AUTO_CREATE_DB` is disabled. All schema updates must be applied via `flask db upgrade`. The deployment workflow automatically handles baseline auto-stamping if upgrading an unversioned database.

---

## API Surface & Authentication

The REST API is mounted at `/api/` with interactive OpenAPI documentation available at `/api/docs/`.

### Authorization Scheme
- **Admin Session Required**: Accessible only by authenticated administrators in active browser sessions.
- **Device Bearer Token Required**: Requires `Authorization: Bearer <DEVICE_API_TOKEN>` header for edge devices.
- **Session or Device Token Required**: Accepts either authenticated browser session or valid device bearer token.

| Endpoint | Method | Required Authorization | Purpose |
| :--- | :---: | :---: | :--- |
| `/api/studentlist` | `GET` | Admin Session | Retrieve registered student profiles |
| `/api/students/<StudID>` | `GET` | Admin Session | Retrieve specific student details |
| `/api/stafflist` | `GET` | Admin Session | Retrieve staff member profiles |
| `/api/staff/<StaffID>` | `GET` | Admin Session | Retrieve specific staff details |
| `/api/roomlist` | `GET` | Device Bearer Token | Retrieve rooms and status |
| `/api/rbooklists` | `GET` | Device Bearer Token | Retrieve upcoming room bookings |
| `/api/RoomBookings/<RBookID>` | `GET` | Admin Session | Retrieve specific booking details |
| `/api/accesslogs` | `GET` | Admin Session | Retrieve historical access logs |
| `/api/accesslogs` | `POST` | Device Bearer Token | Post room access event from edge device |
| `/api/faces` | `GET` | Device Bearer Token | Download face training dataset (`.npz`) |
| `/api/facesembeds` | `GET` | Device Bearer Token | Download FaceNet embeddings (`.npz`) |
| `/api/recognize_frame` | `POST` | Session or Device Token | Process webcam frame for identification |

---

## Testing

Tests are executed with `pytest` from the `aria-app/` directory:

```bash
cd aria-app

# Run all test suites
pytest

# Run specific test suites
pytest tests/unit/
pytest tests/integration/
pytest tests/test_security.py
pytest tests/test_ui_rollout.py

# Run Playwright E2E browser smoke tests
pytest tests/e2e/
```

### Test Configuration
The test harness in [`aria-app/tests/conftest.py`](file:///home/nian014/projects/ARIA/aria-app/tests/conftest.py) uses an isolated in-memory SQLite database, disables background threads (`FLASK_SKIP_BACKGROUND_THREADS=1`), and provides fixtures for student, staff, admin, and room entities.

---

## Deployment & Production Architecture

### Production Environment Variables
```bash
FLASK_ENV=production
SECRET_KEY=<generate-strong-random-key>
DATABASE_URL=postgresql+psycopg2://user:password@db-host:5432/ariadb
REDIS_URL=redis://redis-host:6379/0
DEVICE_API_TOKEN=<secure-device-token>
AUTO_CREATE_DB=false
SESSION_COOKIE_SECURE=true
RATELIMIT_STORAGE_URI=redis://redis-host:6379/0
```

### Production Components
- **Application Server**: Gunicorn with multi-worker configuration ([`aria-app/gunicorn.conf.py`](file:///home/nian014/projects/ARIA/aria-app/gunicorn.conf.py)).
- **Reverse Proxy**: Caddy with automated HTTPS, CSP headers, and static caching ([`aria-app/Caddyfile`](file:///home/nian014/projects/ARIA/aria-app/Caddyfile)).
- **Process Manager**: systemd service unit ([`aria-app/aria.service`](file:///home/nian014/projects/ARIA/aria-app/aria.service)).
- **CI/CD Pipeline**: GitHub Actions workflow ([`.github/workflows/deploy.yml`](file:///home/nian014/projects/ARIA/.github/workflows/deploy.yml)) providing automated testing, SSH deployment, migration execution, and systemd service reloads.
- **Database Hardening**: Optional Row Level Security (RLS) enforcement via [`supabase/rls_lockdown.sql`](file:///home/nian014/projects/ARIA/supabase/rls_lockdown.sql).

---

## License

See [`LICENSE`](file:///home/nian014/projects/ARIA/LICENSE) for details.
