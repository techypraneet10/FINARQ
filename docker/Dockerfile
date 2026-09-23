# ==============================================================================
# Multi-stage Hardened Production Dockerfile for Financial RAG Platform
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build & Dependency Resolution Stage
# ------------------------------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build tools and header packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated isolated virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy package specifications and source files
COPY pyproject.toml README.md /app/
COPY src /app/src

# Upgrade pip and install package
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir .

# ------------------------------------------------------------------------------
# Stage 2: Minimal Hardened Runtime Stage
# ------------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

# Install minimal OS dependencies needed for runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root system user & group (UID/GID 10001)
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create writable storage directory for local fallback and set permissions
RUN mkdir -p /app/data/storage /tmp && \
    chown -R appuser:appgroup /app /tmp

# Copy application source, migrations, and scripts
COPY --chown=appuser:appgroup src/ /app/src/
COPY --chown=appuser:appgroup scripts/ /app/scripts/
COPY --chown=appuser:appgroup alembic.ini /app/alembic.ini
COPY --chown=appuser:appgroup .env.example /app/.env.example
COPY --chown=appuser:appgroup docker/entrypoint.sh /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh

# Set security, locale, and Python runtime flags
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    APP_HOST=0.0.0.0 \
    APP_PORT=8000

# Switch to non-root user
USER 10001:10001

# Liveness probe checking /health endpoint
HEALTHCHECK --interval=20s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:' + str(__import__('os').environ.get('APP_PORT', 8000)) + '/health')" || exit 1

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["api"]
