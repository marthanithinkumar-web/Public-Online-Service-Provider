import multiprocessing
import os


# Two small worker processes with two threads each provide useful concurrency
# on modest Render instances without opening an excessive number of database
# connections. Production can tune these values through environment variables.
workers = max(1, int(os.getenv('WEB_CONCURRENCY', '2')))
threads = max(1, int(os.getenv('GUNICORN_THREADS', '2')))
worker_class = 'gthread'
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
timeout = max(30, int(os.getenv('GUNICORN_TIMEOUT', '60')))
graceful_timeout = 30
keepalive = 5
max_requests = 1000
max_requests_jitter = 100
accesslog = '-'
errorlog = '-'
capture_output = True
