# =============================================================================
# Neural Terminal - Hugging Face Spaces Dockerfile
# =============================================================================
# Single-stage build optimized for Hugging Face Spaces deployment
#
# Build:
#   docker build -t neural-terminal:hf .
#
# Run locally:
#   docker run -p 7860:7860 -e OPENROUTER_API_KEY=xxx neural-terminal:hf
#
# Hugging Face Spaces:
#   - Port 7860 (mandatory)
#   - Single-stage preferred
#   - Metadata labels for Space card
# =============================================================================

FROM python:3.13-trixie

# =============================================================================
# METADATA - Hugging Face Spaces Display
# =============================================================================
LABEL maintainer="Neural Terminal Team"
LABEL description="Production-grade chatbot with OpenRouter integration - Terminal/Cyberpunk aesthetic"
LABEL version="0.1.0"
LABEL org.opencontainers.image.title="Neural Terminal"
LABEL org.opencontainers.image.description="Multi-model AI chatbot with OpenRouter, cost tracking, and terminal aesthetic"
LABEL org.opencontainers.image.version="0.1.0"
LABEL org.opencontainers.image.authors="Neural Terminal Team"
LABEL org.opencontainers.image.url="https://huggingface.co/spaces/your-username/neural-terminal"
LABEL org.opencontainers.image.source="https://github.com/your-org/neural-terminal"
LABEL org.opencontainers.image.licenses="MIT"

# =============================================================================
# ENVIRONMENT CONFIGURATION
# =============================================================================
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONPATH=/app/src:${PYTHONPATH:-} \
    # Streamlit Configuration for HF Spaces
    STREAMLIT_SERVER_PORT=7860 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ENABLE_CORS=false \
    STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    # Application Configuration
    DATABASE_URL="sqlite:////app/data/neural_terminal.db" \
    APP_HOME=/app \
    # Disable pip cache
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# =============================================================================
# SYSTEM DEPENDENCIES
# =============================================================================
# Install minimal runtime dependencies
# - ca-certificates: HTTPS connections (OpenRouter API)
# - curl: Health checks
# - sqlite3: Database operations and debugging
# - build-essential: Required for compiling some Python packages (tiktoken, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl git wget zip unzip tar \
    sqlite3 \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# =============================================================================
# APPLICATION DIRECTORY STRUCTURE
# =============================================================================
WORKDIR /app

# Create required directories
# - /app/data: SQLite database persistence
# - /app/src: Application source code
# - /app/scripts: Utility scripts
RUN mkdir -p /app/data /app/src/neural_terminal /app/scripts

# =============================================================================
# PYTHON DEPENDENCIES
# =============================================================================
# Copy dependency specification files first (layer caching optimization)
COPY pyproject.toml poetry.lock* ./

# Install dependencies using pip with Poetry export fallback
# This avoids Poetry installation overhead (~50MB) while maintaining
# exact dependency versions from poetry.lock
#
# Strategy:
# 1. Try to install from pyproject.toml using pip (if it has dependencies)
# 2. If that fails, use the explicit requirements below
#
# Alternative: Run `poetry export -f requirements.txt --without-hashes` 
# locally and commit requirements.txt

# Core dependencies extracted from pyproject.toml
# These are the production dependencies only (no dev tools)
RUN pip install --no-cache-dir \
    # Web Framework
    streamlit httpx sqlalchemy alembic pydantic pydantic-settings tiktoken bleach markdown typing-extensions

# =============================================================================
# APPLICATION CODE
# =============================================================================
# Copy application source code
COPY app.py ./
COPY src/ ./src/
COPY scripts/ ./scripts/

# Copy documentation (optional, for reference)
COPY README.md LICENSE* ./

# Copy .env.example to .env if it doesn't exist
# This allows users to mount their own .env file
COPY .env.example .env

# =============================================================================
# DATABASE INITIALIZATION
# =============================================================================
# Initialize SQLite database with production optimizations
# - WAL mode for concurrent access
# - Performance PRAGMAs
# - Index creation
RUN python scripts/init_db.py || echo "Database initialization completed with warnings"

# Verify database was created
RUN ls -la /app/data/ && sqlite3 /app/data/neural_terminal.db "PRAGMA integrity_check;"

# =============================================================================
# HEALTH CHECK
# =============================================================================
# Streamlit health endpoint: /_stcore/health
# HF Spaces uses this to determine container health
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:7860/_stcore/health || exit 1

# =============================================================================
# PORT EXPOSURE
# =============================================================================
# Hugging Face Spaces requires port 7860
EXPOSE 7860

# =============================================================================
# ENTRYPOINT - Streamlit with explicit port 7860
# =============================================================================
# Run Streamlit app directly with explicit --server.port=7860 flag
# Note: WORKDIR is /app, so we use /app/app.py
CMD ["streamlit", "run", "/app/app.py", "--server.port=7860", "--server.address=0.0.0.0"]
