# =============================================================================
# Case-Verify AI — Production Dockerfile
# Op-01 / Hardening Plan
#
# Multi-stage build:
#   Stage 1 (builder) — Install Python deps in a venv
#   Stage 2 (runtime) — Slim image, non-root user, health check
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: builder
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build

# System deps needed to compile some Python packages (bcrypt, Pillow, etc.)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Create venv so we can copy it cleanly into the runtime stage
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.lock .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.lock

# ---------------------------------------------------------------------------
# Stage 2: runtime
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

# Metadata
LABEL maintainer="CaseVerify AI Team"
LABEL description="Professional Legal Consultation System"

# Security: run as non-root
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Runtime system deps (Tesseract for OCR, if pytesseract is used)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        tesseract-ocr \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy venv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Application directory
WORKDIR /app

# Copy application code (respects .dockerignore)
COPY . .

# Create writable data directory for SQLite + logs
RUN mkdir -p /app/data && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Streamlit configuration (headless, no browser, disable CORS for container)
ENV STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    STREAMLIT_SERVER_FILE_WATCHER_TYPE=none \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Expose Streamlit port
EXPOSE 8501

# Health check — uses our health.py module (O-02/O-03)
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD ["python", "health.py"]

# Entrypoint: initialise DB, then launch Streamlit
CMD ["sh", "-c", "python init_database.py && streamlit run app.py"]
