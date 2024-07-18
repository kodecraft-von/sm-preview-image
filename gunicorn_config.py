
accesslog = "logs/gunicorn-access.log"
errorlog = "logs/gunicorn-error.log"
loglevel = "info"

workers = 3
threads = 2
bind = "0.0.0.0:8055" 

# Worker options
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190