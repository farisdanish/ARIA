# ARIA Edge Device Client

Raspberry Pi application for room access control with face recognition.

This client can run in two modes:
1. **Physical Mode (`main.py`)**: Runs on a real Raspberry Pi with GPIO and a live camera.
2. **Simulator Mode (`simulator_main.py`)**: Runs in a Docker container, listening to Redis events and using static test images for recognition.

## Features

- **API Integration**: Fetches bookings, users, and room data from ARIA server
- **Face Recognition**: Uses FaceNet for identity verification
- **Hardware Control**: Controls GPIO relay for door lock/unlock
- **Automatic Locking**: Door auto-locks after configured duration
- **Error Handling**: Graceful handling of API failures and hardware issues

## Requirements

- Raspberry Pi (3 or 4 recommended)
- Raspberry Pi OS (or compatible Linux distribution)
- Camera module or USB webcam
- GPIO relay module for door control
- Python 3.8+

## Installation

1. **Clone the repository** (or copy client directory to Raspberry Pi)

2. **Install dependencies**
   ```bash
   cd aria-app/client
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Set up as systemd service** (optional)
   ```bash
   sudo cp aria-client.service /etc/systemd/system/
   sudo systemctl enable aria-client
   sudo systemctl start aria-client
   ```

## Configuration

Edit `.env` file with your settings:

- `ARIA_API_URL`: Base URL of ARIA server API.
- `REDIS_URL`: URL for the Redis broker (e.g., `redis://redis:6379/0`).
- `RELAY_GPIO_PIN`: GPIO pin number for relay (default: 17).
- `UNLOCK_DURATION_SECONDS`: How long to keep door unlocked (default: 5).
- `FACE_CONFIDENCE_THRESHOLD`: Minimum confidence for face match (0.0-1.0).
- `FACE_DETECTION_COUNT_THRESHOLD`: Number of successful detections required.
- `SIMULATOR_TEST_IMAGES_PATH`: Path to folder containing `.jpg` images for mock recognition.

### Docker Simulator (Recommended for Dev)

The simulator is typically run via `docker-compose`. It listens for Redis events (`watch_room`, `token_validated`) instead of polling.

```bash
# Launched via root docker-compose:
docker-compose up pi-simulator
```

### Physical Raspberry Pi

```bash
# Manual run (uses camera + polling)
python -m client.main
```

### Systemd Service (Pi Only)
```bash
sudo systemctl start aria-client
```

## Hardware Setup

### GPIO Relay Connection

1. Connect relay module to Raspberry Pi:
   - VCC → 5V
   - GND → GND
   - IN → GPIO pin (default: 17)

2. Connect door lock to relay:
   - Follow relay module documentation
   - Ensure proper power supply for lock

### Camera Setup

- USB webcam: Plug in and ensure it's detected (`lsusb`)
- Raspberry Pi Camera: Enable in `raspi-config`

## Architecture

```
client/
├── __init__.py          # Package initialization
├── config.py            # Configuration management
├── api_client.py        # API communication
├── face_recognition.py  # Face recognition logic
├── hardware.py          # GPIO/hardware control (mocked in non-Pi envs)
├── room_monitor.py      # Legacy polling logic (used by main.py)
├── main.py              # Legacy/Physical entry point
├── simulator_main.py    # Modern/Event-driven entry point (Redis)
├── requirements.txt     # Dependencies
└── README.md            # This file
```

## Development

### Testing Without Hardware

The client can run in simulation mode when `RPi.GPIO` is not available:
- GPIO operations are logged but not executed
- Useful for development on non-Raspberry Pi systems

### Debugging

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python -m client.main
```

## Troubleshooting

### Camera Not Detected
- Check camera connection
- Verify camera permissions
- Try different `CAMERA_INDEX` values

### API Connection Failed
- Verify `ARIA_API_URL` is correct
- Check network connectivity
- Ensure server is running and accessible

### Face Recognition Not Working
- Ensure face models are downloaded
- Check model file paths in configuration
- Verify camera is working and lighting is adequate

### GPIO Not Working
- Verify GPIO pin number
- Check relay module connections
- Ensure proper power supply
- Check permissions (may need to run as root or add user to gpio group)

## Security Considerations

- Store API credentials securely
- Use HTTPS for API communication in production
- Restrict file permissions on configuration files
- Consider using API authentication tokens
- Regularly update dependencies

## License

See main project LICENSE file.

