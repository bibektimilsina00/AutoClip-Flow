#!/bin/bash

# Configuration
REDIS_URL="redis://localhost:6379/0"
CELERY_APP="celery_worker.celery_worker"  # Adjust to your actual Celery app location
FASTAPI_APP="app.main:app"  # Replace with the path to your FastAPI instance
UVICORN_PORT=8000
FLOWER_PORT=5555
REDIS_CONTAINER_NAME="redis"  

# Log files
FASTAPI_LOG="logs/fastapi.log"
CELERY_WORKER_LOG="logs/celery_worker.log"
FLOWER_LOG="logs/flower.log"
REDIS_LOG="logs/redis.log"

start_redis() {
    echo "Starting Redis in Docker..."
    docker run --name $REDIS_CONTAINER_NAME -d -p 6379:6379 redis > $REDIS_LOG 2>&1
}

stop_redis() {
    echo "Stopping Redis Docker container..."
    docker stop $REDIS_CONTAINER_NAME
    docker rm $REDIS_CONTAINER_NAME
}

start_fastapi() {
    echo "Starting FastAPI application..."
    nohup uvicorn $FASTAPI_APP --host 0.0.0.0 --port $UVICORN_PORT > $FASTAPI_LOG 2>&1 &
    echo $! > fastapi.pid
}

stop_fastapi() {
    echo "Stopping FastAPI application..."
    if [ -f fastapi.pid ]; then
        kill $(cat fastapi.pid)
        rm fastapi.pid
    else
        echo "FastAPI is not running or PID file not found."
    fi
}

start_celery() {
    echo "Starting Celery worker..."
    nohup celery -A $CELERY_APP worker --loglevel=info > $CELERY_WORKER_LOG 2>&1 &
    echo $! > celery.pid
}

stop_celery() {
    echo "Stopping Celery worker..."
    if [ -f celery.pid ]; then
        kill $(cat celery.pid)
        rm celery.pid
    else
        echo "Celery worker is not running or PID file not found."
    fi
}

start_flower() {
    echo "Starting Flower monitoring tool..."
    nohup celery -A $CELERY_APP flower  > $FLOWER_LOG 2>&1 &
    echo $! > flower.pid
}

stop_flower() {
    echo "Stopping Flower monitoring tool..."
    if [ -f flower.pid ]; then
        kill $(cat flower.pid)
        rm flower.pid
    else
        echo "Flower is not running or PID file not found."
    fi
}

kill_tasks() {
    echo "Killing all tasks..."
    local PROCESS_NAMES=(
        "celery"
        "tail -f fastapi.log"
        "tail -f celery_worker.log"
        "tail -f flower.log"
        "tail -f redis.log"
    )

    for name in "${PROCESS_NAMES[@]}"; do
        pids=$(pgrep -f "$name")
        if [ -n "$pids" ]; then
            echo "Killing processes: $pids"
            kill -9 $pids
        else
            echo "No processes found for: $name"
        fi
    done
}

status() {
    echo "Checking status of all services..."

    if docker ps --filter "name=$REDIS_CONTAINER_NAME" | grep -q $REDIS_CONTAINER_NAME; then
        echo "Redis is running."
    else
        echo "Redis is not running."
    fi

    if [ -f fastapi.pid ] && kill -0 $(cat fastapi.pid) 2>/dev/null; then
        echo "FastAPI is running on port $UVICORN_PORT."
    else
        echo "FastAPI is not running."
    fi

    if [ -f celery.pid ] && kill -0 $(cat celery.pid) 2>/dev/null; then
        echo "Celery worker is running."
    else
        echo "Celery worker is not running."
    fi

    if [ -f flower.pid ] && kill -0 $(cat flower.pid) 2>/dev/null; then
        echo "Flower is running on port $FLOWER_PORT."
    else
        echo "Flower is not running."
    fi
}

start_all() {
    echo "Starting all services..."
    start_redis
    start_fastapi
    start_celery
    start_flower
}

stop_all() {
    echo "Stopping all services..."
    stop_flower
    stop_celery
    stop_fastapi
    stop_redis
}

show_logs() {
    echo "Displaying logs for each service:"
    echo "------ FastAPI Log ------"
    tail -n 20 $FASTAPI_LOG
    echo "------ Celery Worker Log ------"
    tail -n 20 $CELERY_WORKER_LOG
    echo "------ Flower Log ------"
    tail -n 20 $FLOWER_LOG
    echo "------ Redis Log ------"
    tail -n 20 $REDIS_LOG
}

run_detached() {
    echo "Starting all services in detached mode..."
    start_redis
    start_fastapi
    start_celery
    start_flower
    echo "All services started in detached mode."
}

run_non_detached() {
    echo "Starting all services in non-detached (live logs) mode..."
    start_redis
    start_fastapi
    start_celery
    start_flower
    
    # Show live logs for all services
    tail -f $FASTAPI_LOG $CELERY_WORKER_LOG $FLOWER_LOG $REDIS_LOG &
    LOG_PID=$!

    # Listen for input
    while true; do
        read -n 1 -s key  # Read one character without pressing enter
        case "$key" in
            r) 
                echo "Restarting all services..."
                stop_all
                start_all
                ;;
            c)
                echo "Stopping all services..."
                stop_all
                kill $LOG_PID  # Stop the log tailing
                exit 0
                ;;
            k)
                echo "Killing all running tasks..."
                kill_tasks
                ;;
            *) 
                echo "Press 'r' to restart, 'c' to stop, or 'k' to kill tasks."
                ;;
        esac
    done
}

case "$1" in
    start)
        run_non_detached
        ;;
    stop)
        stop_all
        ;;
    restart)
        stop_all
        run_non_detached
        ;;
    status)
        status
        ;;
    logs)
        show_logs
        ;;
    detached)
        run_detached
        ;;
    kill)
        kill_tasks
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|detached|kill}"
        exit 1
        ;;
esac
