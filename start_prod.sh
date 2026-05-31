#!/bin/bash
# Production: Gunicorn with multiple Uvicorn workers
gunicorn main:app -c gunicorn.conf.py
