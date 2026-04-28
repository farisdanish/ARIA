"""Gunicorn settings for ARIA (production: Caddy terminates TLS upstream)."""
workers = 1
threads = 2
worker_class = 'sync'
timeout = 120
keepalive = 5
bind = '127.0.0.1:8000'
accesslog = '/var/log/aria/access.log'
errorlog = '/var/log/aria/error.log'
loglevel = 'info'
capture_output = True
forwarded_allow_ips = '127.0.0.1'
