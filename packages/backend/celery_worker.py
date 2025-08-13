#!/usr/bin/env python3
"""
Celery worker startup script
"""
import os
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.worker.celery_app import celery_app

if __name__ == "__main__":
    celery_app.start()