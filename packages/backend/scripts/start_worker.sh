#!/bin/bash
# Start Celery worker with appropriate settings

# Default queue
celery -A app.worker.celery_app worker \
  --loglevel=info \
  --concurrency=4 \
  --queues=default,email,ai \
  --hostname=worker@%h