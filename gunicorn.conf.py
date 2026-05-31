import multiprocessing
import os

# Render (and Railway/Fly) inject PORT — fall back to 8000 locally
port = os.environ.get("PORT", "8000")

workers = int(os.environ.get("WEB_CONCURRENCY", 1))
worker_class = "uvicorn.workers.UvicornWorker"
bind = f"0.0.0.0:{port}"
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 100
preload_app = True
accesslog = "-"
errorlog = "-"
loglevel = "info"
