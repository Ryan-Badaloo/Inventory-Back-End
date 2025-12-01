#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "Waiting to connect to database...."

# Wait until the DB is ready
until nc -z "$DB_HOST" "$DB_PORT"; do
    echo "Waiting for database connection..."
    sleep 6
done

echo "Database is up"

# Run Alembic migrations
alembic revision --autogenerate
alembic upgrade head

echo "Starting Backend Service..."

# Start the backend with Uvicorn
exec gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --timeout 60