# Stage 1: Build
FROM python:3.11-slim AS build

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Build deps: gcc for native extensions, libpq-dev for psycopg2 (if needed at compile time)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Stage 2: Runtime
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/venv/bin:$PATH"
ENV FLASK_APP=main.py
ENV FLASK_ENV=production
ENV PORT=8080

WORKDIR /app

# Runtime deps: libgl1 + libglib2.0-0 for OpenCV (no libpq5 needed: psycopg2-binary is self-contained)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=build /opt/venv /opt/venv
COPY --from=build /app .

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE $PORT

# 1 worker + 4 threads: prevents duplicate BookingScheduler/RedisSubscriber
# background threads that spawn once per worker in create_app().
CMD gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120 main:app0
