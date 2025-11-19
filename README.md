# ARIA - Library Room Booking & Face Recognition System

A comprehensive Flask-based application for managing library room bookings with integrated face recognition for access control.

## 🚀 Features

- **User Management**: Student, Staff, and Admin roles with role-based access control
- **Room Booking**: Book rooms and events with conflict detection
- **Face Recognition**: Register and recognize faces for automated access control
- **Announcements**: Admin can create and manage announcements
- **Access Logging**: Track room access with email notifications
- **REST API**: Full REST API for integration with external systems (e.g., Raspberry Pi)

## 📋 Requirements

- Python 3.8+
- MySQL 5.7+ or MariaDB
- Webcam (for face recognition features)

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ARIA/aria-app
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Set up the database**
   - Create a MySQL database: `ariadb`
   - Update `DATABASE_URL` in `.env` with your database credentials
   - The application will use the existing schema (no migrations yet)

6. **Run the application**
   ```bash
   python main.py
   ```

   Or using Flask CLI:
   ```bash
   export FLASK_APP=main.py
   export FLASK_ENV=development
   flask run
   ```

## 📁 Project Structure

```
aria-app/
├── config.py                 # Configuration management
├── main.py                   # Application entry point
├── requirements.txt          # Python dependencies
├── website/                  # Main Flask application
│   ├── __init__.py
│   ├── app.py               # Flask app factory
│   ├── models/              # SQLAlchemy models
│   │   ├── user.py
│   │   ├── room.py
│   │   ├── announcement.py
│   │   └── ...
│   ├── routes/              # Route blueprints
│   │   ├── views.py
│   │   ├── auth.py
│   │   ├── face.py
│   │   └── api/
│   ├── services/            # Business logic layer
│   │   ├── auth_service.py
│   │   ├── booking_service.py
│   │   ├── face_service.py
│   │   └── ...
│   ├── utils/               # Utility functions
│   │   ├── file_utils.py
│   │   └── validators.py
│   ├── static/             # Static files
│   └── templates/          # Jinja2 templates
├── client/                   # Edge device client (Raspberry Pi)
│   ├── __init__.py
│   ├── config.py           # Client configuration
│   ├── api_client.py       # API communication
│   ├── face_recognition.py # Face recognition
│   ├── hardware.py         # GPIO/hardware control
│   ├── room_monitor.py     # Booking monitoring
│   ├── main.py             # Main application
│   ├── requirements.txt    # Client dependencies
│   └── README.md           # Client documentation
└── docs/                   # Documentation
```

## 🔧 Configuration

The application uses environment variables for configuration. See `.env.example` for all available options.

### Key Configuration Variables

- `SECRET_KEY`: Flask secret key (required)
- `DATABASE_URL`: MySQL connection string
- `MAIL_USERNAME`: Email username for notifications
- `MAIL_PASSWORD`: Email password/app password
- `FACE_CONFIDENCE_THRESHOLD`: Face recognition confidence threshold (default: 0.85)

## 🏗️ Architecture

### Design Patterns

- **Application Factory**: Flask app created via factory pattern
- **Service Layer**: Business logic separated from routes
- **Repository Pattern**: Data access abstracted through models
- **Blueprint Pattern**: Routes organized into modules

### Key Components

1. **Models**: SQLAlchemy declarative models (replaced automap)
2. **Services**: Business logic layer (auth, bookings, face recognition, etc.)
3. **Routes**: Thin controllers that delegate to services
4. **Utils**: Reusable utility functions

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
- Some Windows-specific paths may need adjustment for Linux deployment
- Database migrations not yet implemented (using existing schema)

## 🔄 Refactoring Status

This codebase has been comprehensively refactored:

✅ **Completed:**
- Configuration management with environment variables
- Proper SQLAlchemy models (replaced automap)
- Service layer for business logic
- Refactored authentication routes
- Refactored API routes
- Face recognition service (removed hard-coded paths)
- File utilities
- Validation utilities
- Logging infrastructure

🔄 **In Progress:**
- Complete views.py refactoring (split into smaller modules)
- Error handling improvements
- Testing suite

📋 **Planned:**
- Database migrations (Alembic)
- Enhanced API documentation
- Docker containerization
- CI/CD pipeline

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
