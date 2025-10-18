#! /usr/bin/env bash

#! /usr/bin/env bash

# Let the DB start (run under uv runner)
uv run python ../backend_pre_start.py

# Run migrations using uv so it uses the project's environment
uv run alembic upgrade head

# Create initial data in DB
uv run python ./initial_data.py
