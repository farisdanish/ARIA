## Library Booking & Face Recognition Refactor Roadmap

### 1. Foundations
- **Architecture Audit**
  - Map every component: Flask app modules, REST namespaces, SQL schemas, face-recognition scripts, Raspberry Pi hardware flow.
  - Draw request lifecycles (browser → Flask route → service → DB → response) to re-familiarize with Flask’s app factory, blueprints, and request context.
  - Inventory credentials, API keys, and hard-coded paths; flag compliance/security issues.
  - Tip: Use a whiteboard or Miro to visualize route/blueprint relationships—it makes Flask’s modular structure easier to grasp again.
- **Flask Refresher & Conventions**
  - Revisit basics: `app = Flask(__name__)`, `@app.route`, blueprints, request context (`request`, `session`), and app factory patterns.
  - Standardize project layout: `app/__init__.py` for factory, `app/routes`, `app/services`, `app/models`, `app/schemas`.
  - Adopt `flask shell` for interactive DB exploration; add `manage.py` CLI (Flask-Script or Flask CLI) for common tasks.
  - Tip: Keep the official Flask documentation open; re-implement a tiny sample route to regain muscle memory before diving into big refactors.
- **Environment & Tooling**
  - Create `.env.example` highlighting required environment variables (DB URL, mail creds, secret key, GPIO toggles).
  - Introduce Poetry or pip-tools for dependency pinning; add `Makefile` (e.g., `make setup`, `make run`, `make test`).
  - Containerize services with Docker Compose: `web`, `db`, `mailhog`, `pi-sim`. Include a README section on starting/stopping containers.
  - Tip: For WSL2, ensure Docker sockets and file permissions are documented; test hot-reload (`flask run --reload`) inside containers.
- **Testing & Quality Gates**
  - Install `pytest`, `pytest-flask`, `pytest-mock`, `coverage`. Configure base fixtures for app + DB.
  - Add `ruff`/`black` for lint/format; `mypy` (or `pyright`) for typing. Wire them into pre-commit.
  - Configure GitHub Actions or GitLab CI to run lint, tests, and build steps on every push.
  - Tip: Start with smoke tests that simply hit key routes; expand coverage as modules stabilize.
- **Documentation & Knowledge Capture**
  - Write an updated high-level README with “How Flask pieces fit together” cheat sheet.
  - Maintain `docs/architecture.md`, `docs/flask-basics.md`, and `docs/refactor-log.md` to track decisions and rekindle familiarity.
  - Schedule weekly note dumps capturing lessons learned as you re-discover the codebase.
  - Tip: Record short Loom videos walking through the code—future you will thank you.

### 2. Data & Configuration Layer
- **Config Management:** Centralize settings using `pydantic-settings` or `dynaconf`; swap hard-coded paths/passwords for environment variables.
- **Database Access:** Replace automap with SQLAlchemy declarative models; add Alembic migrations and database fixtures.
- **Schema Decoupling:** Separate read/write DTOs from ORM models; introduce repository/service layers.

### 3. Web Backend (Flask)
- **Package Layout:** Restructure into `api`, `services`, `repositories`, `schemas`, `routes`, `tasks` modules.
- **Dependency Injection:** Wire services via app factory; isolate side effects (mail, executor, CV jobs).
- **Validation:** Integrate Marshmallow or Pydantic for request/response validation; enforce API versioning.
- **Authentication & Authorization:** Abstract role checks into decorators/policies; centralize session handling.
- **Testing:** Add pytest suite covering routes, services, DB interactions (use factories + sqlite/mariadb container).

### 4. Frontend Templates & UX
- **Template Refactor:** Break large templates into reusable macros/components; remove inline logic.
- **Assets Pipeline:** Move static uploads to configurable storage; adopt build tooling (Webpack/Vite) if modern JS needed.
- **Accessibility & Responsiveness:** Apply consistent styling, form validation, role-based messaging.
- **Client-Side API:** Standardize fetch helpers for new REST contracts; consider SPA migration later.

### 5. API Modernization
- **RESTX Cleanup:** Refine namespaces, schemas, and error handling; add OpenAPI docs with auth + rate limits.
- **New Endpoints:** Provide dedicated booking availability, access-log summary, and face dataset management APIs.
- **Pagination & Filtering:** Implement query params with sensible defaults; document in API spec.

### 6. Face Recognition Pipeline
- **Data Storage:** Store embeddings in database or versioned object storage; track metadata (timestamps, accuracy).
- **Model Lifecycle:** Introduce training job service with status tracking, rollback, and scheduled retrains.
- **Edge Protocol:** Replace manual ngrok with MQTT/WebSocket or signed REST; secure comms via mutual TLS/token.
- **Monitoring:** Log confidence scores, false positives/negatives; surface dashboards for admins.

### 7. Raspberry Pi / Edge Software
- **Project Structure:** Refactor into modules (`config`, `api`, `recognition`, `hardware`, `runner`); add CLI entrypoints.
- **State Management:** Cache bookings locally with expiry; implement reconnection/backoff strategies.
- **Testing & Simulation:** Create unit tests with mocked camera/GPIO; provide simulator for dev machines.
- **Deployment:** Package as systemd service or Docker container; document OTA update process.

### 8. Observability & Ops
- **Logging:** Standardize structured logging (JSON) with correlation IDs across web + Pi.
- **Metrics:** Expose Prometheus metrics (booking counts, auth latency, recognition success).
- **Alerting:** Configure email/SMS alerts for camera failures, API downtime, low confidence rates.
- **Security Review:** Run dependency scans, secrets scanning, threat modeling, pen-test checklist.

### 9. Documentation & Onboarding
- **Developer Guide:** Update README with architecture diagrams, setup steps, coding standards.
- **Runbooks:** Create troubleshooting guides for hardware, API, and training failures.
- **User Manuals:** Refresh role-specific walkthroughs (admin, staff, student).
- **Knowledge Transfer:** Record ADRs for architectural decisions; plan handoff sessions.

### 10. Execution Strategy
- **Prioritize:** Start with configuration, DB models, and API stabilization before CV pipeline.
- **Iterate:** Deliver in 2–3 week sprints; ensure backward compatibility with feature toggles.
- **Review:** Peer review every PR; maintain regression checklist after each sprint.
- **Measure:** Define KPIs (setup time, test coverage, false unlock rate) and track improvements.

