workers = 1
accesslog = '-'
errorlog = '-'
#loglevel = 'debug'
access_log_format = '%({x-forwarded-for}i)s %(l)s %(t)s %(r)s %(s)s %(b)s %(f)s %(a)s'
bind = ['0.0.0.0:8080']

# Filter healthcheck requests from gunicorn output
import logging

class HealthCheckFilter(logging.Filter):
    def filter(self, record):
        return 'GET /healthz ' not in record.getMessage() and 'GET /health ' not in record.getMessage()

def post_fork(server, worker):
    logger = logging.getLogger('gunicorn.access')
    logger.addFilter(HealthCheckFilter())
