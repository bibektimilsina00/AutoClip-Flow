# Use an official Python runtime as a parent image
FROM python:3.12-alpine

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    curl \
    make \
    openssl-dev


RUN apk add --no-cache \
    xvfb \
    chromium \
    chromium-chromedriver \
    && rm -rf /var/cache/apk/*


# Install Poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python3 && \
    ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry && \
    poetry config virtualenvs.create false

# Copy poetry files
COPY ./pyproject.toml ./poetry.lock* /app/

# Install dependencies
ARG INSTALL_DEV=false
RUN sh -c "if [ $INSTALL_DEV == 'true' ]; then poetry install --no-root; else poetry install --no-root --only main; fi"

ENV PYTHONPATH=/app

# Copy application code
COPY . /app/


# Clean up build dependencies (optional but recommended)
RUN apk del gcc musl-dev libffi-dev && rm -rf /var/cache/apk/*

EXPOSE 8000
