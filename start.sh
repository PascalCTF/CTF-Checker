#!/bin/sh

# Start Gunicorn
gunicorn --bind 0.0.0.0:5000 --reuse-port "src.main:app" &

# Start the scheduler
python src/run_scheduler.py
