# deployment/Dockerfile
FROM python:3.11-slim-bullseye

# System dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    postgresql-client \
    redis-tools \
    git \
    curl \
    vim \
    htop \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -m -u 1000 claude && \
    mkdir -p /app && \
    chown -R claude:claude /app

# Switch to app directory
WORKDIR /app

# Python dependencies - copy requirements first for better caching
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy requirements for different phases
COPY requirements/ /app/requirements/
RUN pip install --no-cache-dir -r requirements/requirements_phase1.txt

# Application code
COPY --chown=claude:claude src/ /app/src/
COPY --chown=claude:claude configs/ /app/configs/
COPY --chown=claude:claude scripts/ /app/scripts/

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/memories && \
    chown -R claude:claude /app/logs /app/data /app/memories

# Environment variables
ENV PYTHONPATH=/app
ENV CLAUDE_AGI_ENV=production

# Switch to non-root user
USER claude

# Expose ports
EXPOSE 8000 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run application
CMD ["python", "-m", "src.main"]