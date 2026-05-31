#!/bin/bash
# Dev: single worker with hot reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
