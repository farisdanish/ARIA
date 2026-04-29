# ARIA

ARIA is a Flask application for library room booking and room access control. The current implementation combines a server-rendered web app, a Flask-RESTX API, Redis-backed background workflows, and a Raspberry Pi client or simulator for door access.

This README covers the repository as it exists today. For the edge client, see `aria-app/client/README.md`.

## What The System Currently Does

- Student, staff, and admin accounts with role-based dashboards
- Room and event booking flows with conflict checks
- QR-based check-in for bookings
- Face registration and face recognition using OpenCV, Keras FaceNet, and a classifier trained from stored face images
- Access logging plus optional email notifications
- Redis pub/sub between the Flask app and the edge device
- Background booking notifications and hourly guest-face cleanup
- Local Docker Compose stack with Postgres, Redis, the Flask app, and a Pi simulator

## Repository Layout

```text
ARIA/
├── README.md
├── docker-compose.yml
├── render.yaml
├── aria-app/
│   ├── main.py
│   ├── config.py
│   ├── requirements.txt
│   ├── gunicorn.conf.py
│   ├── aria.service
│   ├── Caddyfile
│   ├── client/
│   └── website/
│       ├── app.py
│       ├── extensions.py
│       ├── models/
│       ├── routes/
│       ├── services/
│       ├── schemas/
│       ├── static/
│       ├── templates/
│       └── utils/
├── pi-simulator/
└── RaspPiScript/
```

Key directories:

- `aria-app/website/` holds the Flask app, blueprints, models, services, templates, and static assets.
- `aria-app/client/` holds the Raspberry Pi client and simulator-specific client code.
- `pi-simulator/test_images/` is used by the simulator container.
- `RaspPiScript/` contains older Pi-side scripts kept alongside the newer client package.

## Runtime Architecture

The Flask app is created in `aria-app/website/app.py` and started from `aria-app/main.py`.

Current runtime pieces:

- Flask web app with blueprints for home, auth, bookings, rooms, announcements, face routes, and `/api`
- SQLAlchemy models for users, rooms, bookings, faces, access logs, reports, feedback, guests, and announcements
- Flask-Limiter for global and route-specific rate limits
- APScheduler background jobs from `aria-app/website/services/scheduler.py`
- Redis subscriber thread from `aria-app/website/services/subscriber.py`

Redis event flow implemented in the repo:

- `watch_room:{room_id}` is published when a booking is approaching.
- `face_matched:{room_id}` is consumed by the Flask app to mark matching bookings as ongoing and log access.
- `token_validated:{room_id}` is published after successful QR check-in so the Pi side can unlock the door.

## Requirements

- Python 3.8+
- PostgreSQL for the normal app flow
- Redis for full functionality; production startup requires it
- Build tools for native Python packages where needed
- Camera access if you want to use live face capture or recognition locally

The app reads its database from `DATABASE_URL`; the documented stack in this repository is PostgreSQL plus Redis. There is no documented local MySQL default in the current implementation.

## Local Setup

```bash
git clone <repository-url>
cd ARIA/aria-app
python -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools
pip install -r requirements.txt
```

Create environment variables for local development:

```bash
SECRET_KEY=change-me
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/ariadb
REDIS_URL=redis://localhost:6379/0
FLASK_ENV=development
```

Useful optional variables from `aria-app/config.py`:

- `SESSION_LIFETIME_MINUTES`
- `MAX_CONTENT_LENGTH`
- `FACE_CONFIDENCE_THRESHOLD`
- `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS`, `MAIL_USE_SSL`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER`
- `ARIA_INSTANCE_DIR`
- `AUTO_CREATE_DB`
- `FLASK_SKIP_BACKGROUND_THREADS`
- `RATELIMIT_STORAGE_URI`

Production guardrails in code:

- `FLASK_ENV=production` requires `SECRET_KEY`, `DATABASE_URL`, and `REDIS_URL`
- non-testing startup requires `DATABASE_URL`
- production forces secure session cookies and uses Redis for limiter storage

## Running The App

From `aria-app/`:

```bash
python main.py
```

The server listens on `0.0.0.0` and defaults to port `5000`.

Optional development seed:

```bash
python seed.py
```

`AUTO_CREATE_DB` defaults to `true`, so the app will call `db.create_all()` on startup unless you disable it.

## Docker Compose

The root [docker-compose.yml](docker-compose.yml) currently starts:

- `db`: Postgres 15
- `redis`: Redis 7
- `flask-app`: Flask server from `aria-app/Dockerfile`
- `pi-simulator`: simulator client from `aria-app/client/Dockerfile.simulator`

Start the local stack from the repository root:

```bash
docker-compose up --build
```

The compose file bind-mounts parts of `website/static`, `website/templates`, and `website/routes` into the Flask container for faster local iteration.

## API Surface

The REST API is mounted at `/api`, with Flask-RESTX docs typically available at `/api/docs/`.

Implemented endpoints in `aria-app/website/routes/api/routes.py` include:

- `GET /api/studentlist`
- `GET /api/students/<StudID>`
- `GET /api/stafflist`
- `GET /api/staff/<StaffID>`
- `GET /api/roomlist`
- `GET /api/rbooklists`
- `GET /api/RoomBookings/<RBookID>`
- `GET /api/accesslogs`
- `POST /api/accesslogs`
- `GET /api/faces`
- `GET /api/facesembeds`
- `POST /api/recognize_frame`

## Access Control Flows

Web-side flows currently implemented:

- Login and logout with Flask-Login session handling
- Student and staff self-registration
- Room and event booking creation
- QR token generation and email delivery on room bookings
- Browser QR check-in at `/checkin/qr`
- Face registration by repeated scanner capture or single uploaded image
- Admin-triggered face model training at `/train_data`

Face data is stored under the app instance directory, not under versioned static assets:

- training images under `instance/MalaysianFacesDB`
- face dataset at `instance/registered-faces-db.npz`
- embeddings at `instance/registered-faces-db-embeddings.npz`

## Testing

From `aria-app/`:

```bash
pytest
```

The test setup in `aria-app/tests/conftest.py` forces `FLASK_SKIP_BACKGROUND_THREADS=1`, uses `create_app('testing')`, creates an in-memory SQLite database, and creates/drops tables per test fixture.

Current repository tests cover:

- basic route accessibility
- login protection
- UI rollout helper behavior

## Deployment Requirements

Basic production deployment requirements for the current implementation:

- Python 3.8+ runtime with the packages from `aria-app/requirements.txt`
- A PostgreSQL database reachable through `DATABASE_URL`
- A Redis instance reachable through `REDIS_URL`
- A strong `SECRET_KEY`
- `FLASK_ENV=production`
- Writable application storage for `instance/`, including uploads and face model artifacts
- A process manager or app server for the Flask app, such as Gunicorn
- A reverse proxy or ingress layer in front of the app for TLS and public HTTP handling

Minimum production environment variables:

```bash
FLASK_ENV=production
SECRET_KEY=<strong-random-value>
DATABASE_URL=postgresql+psycopg2://user:password@host:5432/dbname
REDIS_URL=redis://host:6379/0
```

Recommended production considerations:

- Disable `AUTO_CREATE_DB` after initial provisioning if you want schema changes to stay explicit.
- Store face data and uploads outside the repository.
- Keep Redis persistent and network-restricted, since it is used for pub/sub and production rate limiting.
- Run the app behind HTTPS, because production enables secure session cookies.

## Known Gaps

- Database migrations are not implemented; the app still relies on `db.create_all()` and manual schema updates where needed.
- Some legacy code remains in `website/routes/views.py`, `archive/`, and `RaspPiScript/`.
- Live face recognition and Pi hardware flows still require camera and hardware access to validate fully outside the simulator.

## License

See `LICENSE`.
