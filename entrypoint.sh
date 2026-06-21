#!/bin/sh
set -e

python -c "from database import init_db; init_db()"

exec gunicorn \
  --bind 0.0.0.0:5000 \
  --workers 2 \
  --threads 4 \
  --timeout 60 \
  app:app
