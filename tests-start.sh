#! /usr/bin/env bash
set -e
set -x

# Use uv run to execute Python scripts so they run with the uv runtime
uv run python /app/tests_pre_start.py

bash ./scripts/test.sh "$@"
