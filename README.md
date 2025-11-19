# ARIA - Library Room Booking & Face Recognition System

A comprehensive Flask-based application for managing library room bookings with integrated face recognition for access control.

> **Note:** This README covers the entire ARIA project. For detailed Raspberry Pi client setup and usage, see [`aria-app/client/README.md`](aria-app/client/README.md).

## 🚀 Features

- **User Management**: Student, Staff, and Admin roles with role-based access control
- **Room Booking**: Book rooms and events with conflict detection
- **Face Recognition**: Register and recognize faces for automated access control
- **Announcements**: Admin can create and manage announcements
- **Access Logging**: Track room access with email notifications
- **REST API**: Full REST API for integration with external systems (e.g., Raspberry Pi)

## 📋 Requirements

- Python 3.8+ (Note: Python 3.12+ requires `setuptools` for `distutils` compatibility)
- MySQL 5.7+ or MariaDB
- Webcam (for face recognition features)
- MySQL client development libraries (required for `mysqlclient` package)

## 🛠️ Installation

### Prerequisites

Before installing Python dependencies, you need to install MySQL client development libraries for your operating system. The `mysqlclient` package requires these libraries to compile.

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install default-libmysqlclient-dev build-essential pkg-config python3-dev
```

> **Note:** For Python 3.12 specifically, you may also need `python3.12-dev`:
> ```bash
> sudo apt-get install python3.12-dev
> ```

#### Linux (Fedora/RHEL/CentOS)
```bash
sudo dnf install mysql-devel gcc pkg-config python3-devel
# Or for older systems:
# sudo yum install mysql-devel gcc pkg-config python3-devel
```

#### macOS
```bash
# Using Homebrew (recommended)
brew install mysql pkg-config

# Or using MacPorts
sudo port install mysql8 +universal
```

#### Windows
For Windows, you have two options:

**Option 1: Use pre-compiled wheel (easiest)**
- Download MySQL from [MySQL Installer](https://dev.mysql.com/downloads/installer/)
- Install MySQL Connector/C or MySQL Server (which includes the client libraries)
- Ensure MySQL is added to your system PATH
- Install Visual C++ Build Tools from [Microsoft](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

**Option 2: Use PyMySQL instead (no compilation needed)**
- Replace `mysqlclient==2.2.0` with `PyMySQL==1.1.0` in `requirements.txt`
- Update your `DATABASE_URL` in `.env` from `mysql+mysqldb://` to `mysql+pymysql://`

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
   
   > **Note:** 
   > - If you encounter errors installing `mysqlclient`, ensure you've installed the MySQL client development libraries for your OS (see Prerequisites above).
   > - For Python 3.12+, `setuptools` is required (included in requirements.txt) as `distutils` was removed from the standard library.

4. **Set up environment variables**
   
   Create a `.env` file in the `aria-app/` directory (or set environment variables):
   ```bash
   # Required
   SECRET_KEY=your-secret-key-here
   DATABASE_URL=mysql+mysqldb://user:password@localhost:3306/ariadb
   
   # Optional (with defaults)
   FLASK_ENV=development
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   FACE_CONFIDENCE_THRESHOLD=0.85
   SESSION_LIFETIME_MINUTES=480
   ```
   
   See `config.py` for all available configuration options.

5. **Set up the database**
   - Create a MySQL database: `ariadb`
   - Update `DATABASE_URL` in `.env` with your database credentials
   - The application will use the existing schema (no migrations yet)

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
├── LICENSE                  # License file
├── aria-app/                # Main application directory
│   ├── main.py              # Application entry point
│   ├── config.py            # Configuration management
│   ├── requirements.txt     # Python dependencies
│   ├── website/             # Main Flask application
│   │   ├── __init__.py
│   │   ├── app.py           # Flask app factory
│   │   ├── models/          # SQLAlchemy models
│   │   │   ├── base.py      # Database initialization
│   │   │   ├── user.py      # Student, Staff, Admin models
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
│   │   │   ├── face_training.py
│   │   │   ├── room_service.py
│   │   │   ├── announcement_service.py
│   │   │   └── mail_service.py
│   │   ├── schemas/         # API schemas
│   │   ├── utils/           # Utility functions
│   │   │   ├── file_utils.py
│   │   │   └── validators.py
│   │   ├── static/          # Static files (CSS, JS, images, uploads)
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

**Required:**
- `SECRET_KEY`: Flask secret key (required for sessions)
- `DATABASE_URL`: MySQL connection string (default: `mysql+mysqldb://root:@localhost:3306/ariadb`)

**Optional (with defaults):**
- `FLASK_ENV`: Environment mode (`development`, `production`, `testing`)
- `FLASK_DEBUG`: Enable debug mode (`True`/`False`)
- `MAIL_SERVER`: SMTP server (default: `smtp.gmail.com`)
- `MAIL_PORT`: SMTP port (default: `465`)
- `MAIL_USE_SSL`: Use SSL for mail (default: `True`)
- `MAIL_USERNAME`: Email username for notifications
- `MAIL_PASSWORD`: Email password/app password
- `FACE_CONFIDENCE_THRESHOLD`: Face recognition confidence threshold (default: `0.85`)
- `SESSION_LIFETIME_MINUTES`: Session duration in minutes (default: `480`)
- `MAX_CONTENT_LENGTH`: Max upload size in bytes (default: `16777216` = 16 MB)

All configuration is managed through `config.py` using environment variables.

## 🏗️ Architecture

### Design Patterns

- **Application Factory**: Flask app created via factory pattern
- **Service Layer**: Business logic separated from routes
- **Repository Pattern**: Data access abstracted through models
- **Blueprint Pattern**: Routes organized into modules

### Key Components

1. **Models**: SQLAlchemy declarative models organized by domain (user, room, face, etc.)
2. **Services**: Business logic layer that handles complex operations (auth, bookings, face recognition, etc.)
3. **Routes**: Thin controllers organized as Flask blueprints that delegate to services
4. **Utils**: Reusable utility functions for file handling, validation, etc.
5. **Configuration**: Centralized configuration management via `config.py` with environment variable support

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
3. Model files are saved in `static/` directory

## 🔌 Edge Device Client

The Raspberry Pi client (`aria-app/client/`) provides:
- Room booking monitoring
- Face recognition for access control
- GPIO relay control for door locks
- Automatic access logging

See `client/README.md` for installation and configuration details.

## 🧪 Testing

```bash
# Run tests (when implemented)
pytest

# With coverage
pytest --cov=website
```

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

### MySQL Client Library Issues

**Error: `Can not find valid pkg-config name` or `mysql_config not found`**

This means the MySQL client development libraries are not installed. Follow the Prerequisites section above for your operating system.

**Error: `Python.h: No such file or directory`**

This means Python development headers are missing. Install them:
- **Ubuntu/Debian:** `sudo apt-get install python3-dev` (or `python3.12-dev` for Python 3.12)
- **Fedora/RHEL:** `sudo dnf install python3-devel`
- **macOS:** Usually included with Xcode Command Line Tools (`xcode-select --install`)

**Windows: Alternative Solution**
If you continue to have issues on Windows, consider using PyMySQL instead:
1. Edit `requirements.txt` and replace `mysqlclient==2.2.0` with `PyMySQL==1.1.0`
2. Update your `.env` file: change `DATABASE_URL` from `mysql+mysqldb://` to `mysql+pymysql://`
3. Reinstall dependencies: `pip install -r requirements.txt`

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

### Database Connection Issues

Ensure MySQL/MariaDB is running and accessible:
- **Linux/macOS:** `sudo systemctl status mysql` or `brew services list`
- **Windows:** Check Services panel for MySQL service

Verify your `DATABASE_URL` in `.env` matches your MySQL setup.

## 🔄 Refactoring Status

This codebase has been comprehensively refactored:

✅ **Completed:**
- Configuration management with environment variables (`config.py`)
- Proper SQLAlchemy declarative models (replaced automap)
- Service layer for business logic separation
- Refactored authentication routes (`auth.py`)
- Refactored API routes (Flask-RESTX with Swagger docs)
- Face recognition service (removed hard-coded paths)
- Route organization into focused blueprints (home, auth, face, announcements, rooms, bookings)
- File utilities and validation utilities
- Logging infrastructure
- Cross-platform path handling (removed Windows-specific paths)

🔄 **In Progress:**
- Complete `views.py` refactoring (legacy routes being migrated)
- Error handling improvements
- Testing suite

📋 **Planned:**
- Database migrations (Alembic)
- Enhanced API documentation
- Docker containerization
- CI/CD pipeline
- Environment variable template (`.env.example`)

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
