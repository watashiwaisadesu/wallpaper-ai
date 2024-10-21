#!/bin/bash

# Wait for PostgreSQL to be ready
while ! nc -z db 5432; do
  echo "Waiting for PostgreSQL..."
  sleep 2
done

# Run alembic upgrade
echo "PostgreSQL is up - executing command"
