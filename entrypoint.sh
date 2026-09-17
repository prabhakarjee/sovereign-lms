#!/bin/bash
set -e

echo "=== Sovereign Django LMS Boot Sequence ==="

# Wait for Nexus PostgreSQL
if [ -n "$DB_HOST" ] && [ "$DB_HOST" != "localhost" ]; then
    echo "Waiting for central database at $DB_HOST:${DB_PORT:-5432}..."
    while ! timeout 1 bash -c "cat < /dev/null > /dev/tcp/${DB_HOST}/${DB_PORT:-5432}" 2>/dev/null; do
        sleep 1
    done
    echo "PostgreSQL reachable!"
fi

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Collecting static assets..."
python manage.py collectstatic --noinput

echo "Seeding initial admin and training curriculums..."
python manage.py seed_initial_data

echo "Starting Gunicorn server..."
exec gunicorn sovereign_lms.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
