#!/usr/bin/env bash

# Minimal service manager: start_all and stop_all (plus status and logs)
# Designed to be simple and easy to reason about. It starts Redis (Docker),
# FastAPI and a Celery worker using nohup and records PID files so stop is easy.

set -eu

ROOT_DIR=$(cd "$(dirname "$0")" && pwd)
LOG_DIR="$ROOT_DIR/logs"
mkdir -p "$LOG_DIR"

# Config (edit if needed)
REDIS_CONTAINER_NAME="video_uploder-redis-1"
REDIS_IMAGE="redis:latest"
FASTAPI_APP="app.main:app"
CELERY_APP="celery_worker.celery_worker"
UVICORN_PORT=8000
FLOWER_PORT=5555

FASTAPI_LOG="$LOG_DIR/fastapi.log"
CELERY_LOG="$LOG_DIR/celery_worker.log"
FLOWER_LOG="$LOG_DIR/flower.log"
REDIS_LOG="$LOG_DIR/redis.log"

FASTAPI_PID_FILE="$ROOT_DIR/fastapi.pid"
CELERY_PID_FILE="$ROOT_DIR/celery.pid"
FLOWER_PID_FILE="$ROOT_DIR/flower.pid"

# External Redis: if EXTERNAL_REDIS is set, the script will not manage Docker Redis.
# Set REDIS_URL externally, e.g. EXTERNAL_REDIS=1 REDIS_URL=redis://host:6379 ./services.sh start
REDIS_URL=${REDIS_URL:-"redis://localhost:6379/0"}
export CELERY_BROKER_URL="$REDIS_URL"
export CELERY_RESULT_BACKEND="$REDIS_URL"
EXTERNAL_REDIS=${EXTERNAL_REDIS:-}

start_redis() {
    if [ -n "$EXTERNAL_REDIS" ]; then
        echo "EXTERNAL_REDIS set; skipping starting Docker Redis. Using REDIS_URL=$REDIS_URL"
        return 0
    fi
    if command -v docker >/dev/null 2>&1; then
        if docker ps --format '{{.Names}}' | grep -q "^${REDIS_CONTAINER_NAME}$"; then
            echo "Redis container exists, starting..."
            docker start "$REDIS_CONTAINER_NAME" >> "$REDIS_LOG" 2>&1 || true
        else
            echo "Running Redis container..."
            docker run --name "$REDIS_CONTAINER_NAME" -d -p 6379:6379 "$REDIS_IMAGE" >> "$REDIS_LOG" 2>&1
        fi
    else
        echo "Docker not found; please run Redis separately (or set EXTERNAL_REDIS=1 and REDIS_URL)." >&2
        return 1
    fi
}

stop_redis() {
    if [ -n "$EXTERNAL_REDIS" ]; then
        echo "EXTERNAL_REDIS set; not stopping external Redis."
        return 0
    fi
    if command -v docker >/dev/null 2>&1; then
        if docker ps -a --format '{{.Names}}' | grep -q "^${REDIS_CONTAINER_NAME}$"; then
            echo "Stopping Redis container..."
            docker stop "$REDIS_CONTAINER_NAME" >> "$REDIS_LOG" 2>&1 || true
            docker rm "$REDIS_CONTAINER_NAME" >> "$REDIS_LOG" 2>&1 || true
        else
            echo "Redis container not found; nothing to stop"
        fi
    else
        echo "Docker not found; can't stop container."
    fi
}

start_fastapi() {
    echo "Starting FastAPI (uvicorn)..."
        # Note: --reload spawns a subprocess which can bypass our redirection; avoid it for service management.
        nohup env CELERY_BROKER_URL="$REDIS_URL" CELERY_RESULT_BACKEND="$REDIS_URL" uv run uvicorn $FASTAPI_APP --host 0.0.0.0 --port $UVICORN_PORT > "$FASTAPI_LOG" 2>&1 &
    echo $! > "$FASTAPI_PID_FILE"
}

stop_fastapi() {
    if [ -f "$FASTAPI_PID_FILE" ]; then
        PID=$(cat "$FASTAPI_PID_FILE")
        echo "Stopping FastAPI pid $PID"
        kill "$PID" >/dev/null 2>&1 || true
        sleep 1
        kill -0 "$PID" >/dev/null 2>&1 || true && kill -9 "$PID" >/dev/null 2>&1 || true
        rm -f "$FASTAPI_PID_FILE"
    else
        echo "FastAPI PID file not found; attempting to stop by name..."
        PIDS=$(pgrep -f "uvicorn") || true
        if [ -n "${PIDS:-}" ]; then
            echo "Killing uvicorn pids: $PIDS"
            kill $PIDS || kill -9 $PIDS || true
        else
            echo "No uvicorn processes found."
        fi
    fi
    # Also attempt to kill any leftover uv run supervisor/parent processes and children
    # This handles cases where uvicorn was started with --reload or by other wrappers.
    REMAINING=$(pgrep -f "uv run uvicorn|uvicorn" ) || true
    if [ -n "${REMAINING:-}" ]; then
        echo "Cleaning up additional FastAPI related pids: $REMAINING"
        kill $REMAINING || kill -9 $REMAINING || true
    fi
}

start_celery() {
    echo "Starting Celery worker..."
    nohup env CELERY_BROKER_URL="$REDIS_URL" CELERY_RESULT_BACKEND="$REDIS_URL" uv run celery -A $CELERY_APP worker --loglevel=info > "$CELERY_LOG" 2>&1 &
    echo $! > "$CELERY_PID_FILE"
}

start_flower() {
    echo "Starting Flower monitoring..."
    nohup env CELERY_BROKER_URL="$REDIS_URL" CELERY_RESULT_BACKEND="$REDIS_URL" uv run celery -A $CELERY_APP flower --port=$FLOWER_PORT > "$FLOWER_LOG" 2>&1 &
    echo $! > "$FLOWER_PID_FILE"
}

stop_celery() {
    if [ -f "$CELERY_PID_FILE" ]; then
        PID=$(cat "$CELERY_PID_FILE")
        echo "Stopping Celery pid $PID"
        kill "$PID" >/dev/null 2>&1 || true
        sleep 1
        kill -0 "$PID" >/dev/null 2>&1 || true && kill -9 "$PID" >/dev/null 2>&1 || true
        rm -f "$CELERY_PID_FILE"
    else
        echo "Celery PID file not found; attempting to stop by name..."
        PIDS=$(pgrep -f "celery") || true
        if [ -n "${PIDS:-}" ]; then
            echo "Killing celery pids: $PIDS"
            kill $PIDS || kill -9 $PIDS || true
        else
            echo "No celery processes found."
        fi
    fi
}

stop_flower() {
    if [ -f "$FLOWER_PID_FILE" ]; then
        PID=$(cat "$FLOWER_PID_FILE")
        echo "Stopping Flower pid $PID"
        kill "$PID" >/dev/null 2>&1 || true
        sleep 1
        kill -0 "$PID" >/dev/null 2>&1 || true && kill -9 "$PID" >/dev/null 2>&1 || true
        rm -f "$FLOWER_PID_FILE"
    else
        echo "Flower PID file not found; attempting to stop by name..."
        PIDS=$(pgrep -f "flower|celery.*flower") || true
        if [ -n "${PIDS:-}" ]; then
            echo "Killing flower pids: $PIDS"
            kill $PIDS || kill -9 $PIDS || true
        else
            echo "No flower processes found."
        fi
    fi
}

start_all() {
    echo "Starting all services..."
    start_redis || true
    start_fastapi || true
    start_celery || true
    start_flower || true
    echo "All start commands issued. Check logs in $LOG_DIR"
}

stop_all() {
    echo "Stopping all services..."
    stop_flower || true
    stop_celery || true
    stop_fastapi || true
    stop_redis || true
    echo "All stop commands issued."
}

tail_logs() {
    # Ensure services are started (but don't fail if already running)
    start_redis || true
    start_fastapi || true
    start_celery || true
    start_flower || true

    echo "Tailing logs. Press Ctrl-C to stop tailing (services will keep running)."
    # Use -F to follow even if files rotate
    tail -F "$FASTAPI_LOG" "$CELERY_LOG" "$FLOWER_LOG" "$REDIS_LOG" &
    TAIL_PID=$!

    # Ensure tail is killed on exit of this function (if user presses Ctrl-C)
    trap "kill $TAIL_PID >/dev/null 2>&1 || true; exit 0" INT TERM

    wait $TAIL_PID
}

tail_fastapi() {
    # Ensure services are started
    start_redis || true
    start_fastapi || true
    start_celery || true
    start_flower || true

    echo "Tailing FastAPI log. Press Ctrl-C to stop (services will keep running)."
    tail -F "$FASTAPI_LOG" &
    TAIL_PID=$!

    trap "kill $TAIL_PID >/dev/null 2>&1 || true; exit 0" INT TERM

    wait $TAIL_PID
}

status() {
    echo "Status overview:"
    if docker ps --filter "name=$REDIS_CONTAINER_NAME" | grep -q "$REDIS_CONTAINER_NAME"; then
        echo "Redis: running (docker)"
    else
        echo "Redis: not running (docker)"
    fi
    if [ -f "$FASTAPI_PID_FILE" ] && kill -0 $(cat "$FASTAPI_PID_FILE") 2>/dev/null; then
        echo "FastAPI: running (pid $(cat $FASTAPI_PID_FILE))"
    else
        echo "FastAPI: not running"
    fi
    if [ -f "$CELERY_PID_FILE" ] && kill -0 $(cat "$CELERY_PID_FILE") 2>/dev/null; then
        echo "Celery: running (pid $(cat $CELERY_PID_FILE))"
    else
        echo "Celery: not running"
    fi
}

case "${1:-tail}" in
    start)
        # start and show FastAPI logs continuously
        tail_fastapi
        ;;
    stop)
        stop_all
        ;;
    restart)
        stop_all
        start_all
        ;;
    status)
        status
        ;;
    tail)
        tail_logs
        ;;
    detached)
        start_all
        echo "Started services in detached mode. Check logs in $LOG_DIR"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|tail|detached}"
        exit 1
        ;;
esac
