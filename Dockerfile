FROM python:3.13-slim-bookworm

# Build-time arguments for environment configuration
ARG ENV=production
ARG APP_VERSION=latest
ARG GIT_BRANCH=unknown

# Install build dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libpq-dev \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN adduser --disabled-password --gecos "" appuser

# Set up working directory
WORKDIR /app

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
RUN uv --version

# Create directories with correct permissions
RUN mkdir -p /home/appuser/.cache/uv /app/.venv \
    && chown -R appuser:appuser /home/appuser /app

# Copy ALL application files first
COPY --chown=appuser:appuser . .

# Add environment label
LABEL environment=${ENV}
LABEL version=${APP_VERSION}
LABEL git_branch=${GIT_BRANCH}
LABEL maintainer="AutoClipFlow Team"

# Switch to non-root user for dependency installation
USER appuser

# Install dependencies based on environment
RUN if [ "$ENV" = "development" ] || [ "$ENV" = "staging" ]; then \
    uv sync; \
    else \
    uv sync --frozen; \
    fi

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Configure environment
ENV PYTHONPATH="/app" \
    PORT=8080 \
    PATH="/app/.venv/bin:$PATH" \
    HOME="/home/appuser" \
    APP_ENV=${ENV}

# Expose port
EXPOSE 8080

# Add health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health/ || exit 1

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
