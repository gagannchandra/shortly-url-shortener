# ── Build stage ────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps into a venv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Runtime stage ───────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Security: run as non-root
RUN groupadd -r shortly && useradd -r -g shortly shortly

WORKDIR /app

# Copy venv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=shortly:shortly . .

# Switch to non-root user
USER shortly

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

# Gunicorn configuration
ENV GUNICORN_WORKERS=2
ENV GUNICORN_TIMEOUT=30
ENV GUNICORN_BIND=0.0.0.0:8000

CMD gunicorn \
    --workers ${GUNICORN_WORKERS} \
    --worker-class sync \
    --timeout ${GUNICORN_TIMEOUT} \
    --bind ${GUNICORN_BIND} \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --forwarded-allow-ips="*" \
    "run:app"
