#!/bin/bash
set -e

echo "Waiting for PostgreSQL to become available..."

until nc -z "$DB_HOST" "$DB_PORT"; do
  echo "Database unavailable, waiting..."
  sleep 3
done

echo "Database is up!"

echo "Running migrations..."
alembic upgrade head

echo "Starting backend..."
exec gunicorn main:app -w 1 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --timeout 60