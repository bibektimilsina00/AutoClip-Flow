#!/bin/sh

# Start the FastAPI application using Gunicorn
exec uvicorn app.app.main:app --host 0.0.0.0 --port 4000
