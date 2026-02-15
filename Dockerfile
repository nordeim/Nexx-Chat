# syntax=docker/dockerfile:1
# =============================================================================
# Neural Terminal - Production Dockerfile
# =============================================================================
# Multi-stage build optimized for Streamlit applications
# 
# Build:
#   docker build -t neural-terminal:latest .
#
# Run:
#   docker run -p 8501:8501 -e OPENROUTER_API_KEY=xxx neural-terminal:latest
#
# With persistent storage:
#   docker run -p 8501:8501 -v $(pwd)/data:/app/data neural-terminal:latest
# =============================================================================

# -----------------------------------------------------------------------------
# STAGE 1: Builder
# -----------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==1.8.5

# Set Poetry to not create virtualenv (we're in a container)
RUN poetry config virtualenvs.create false

WORKDIR /app

# Copy dependency files first (for layer caching)
COPY pyproject.toml poetry.lock ./

# Install production dependencies
# --no-dev: Skip dev dependencies
# --no-interaction: Don't ask questions
# --no-ansi: Disable colored output
RUN poetry install --no-dev --no-interaction --no-ansi --no-root

# -----------------------------------------------------------------------------
# STAGE 2: Runtime
# -----------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS runtime

LABEL maintainer="Neural Terminal Team"
LABEL description="Production-grade chatbot with OpenRouter integration"
LABEL version="0.1.0"

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ENABLE_CORS=false \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    DATABASE_URL="sqlite:////app/data/neural_terminal.db" \
    APP_HOME=/app \
    USER=neural

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Security updates
    ca-certificates \
    # Health checks
    curl \
    # SQLite tooling for debugging
    sqlite3 \
    # Cleanup
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd --gid 1000 ${USER} && \
    useradd --uid 1000 --gid ${USER} --shell /bin/bash --create-home ${USER}

# Create app directories
RUN mkdir -p /app/data /app/src && \
    chown -R ${USER}:${USER} /app

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=${USER}:${USER} app.py ./
COPY --chown=${USER}:${USER} src/ ./src/
COPY --chown=${USER}:${USER} scripts/ ./scripts/
COPY --chown=${USER}:${USER} README.md LICENSE ./

# Copy entrypoint script
COPY --chown=${USER}:${USER} docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Initialize database for production
RUN python scripts/init_db.py || true

# Switch to non-root user
USER ${USER}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${STREAMLIT_SERVER_PORT}/_stcore/health || exit 1

# Expose Streamlit port
EXPOSE ${STREAMLIT_SERVER_PORT}

# Volume for persistent data (conversations, settings)
VOLUME ["/app/data"]

# Entrypoint
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["start"]
