#!/bin/sh

python src/run_scheduler.py &
gunicorn --bind 0.0.0.0:5000 --reuse-port "src.main:app"