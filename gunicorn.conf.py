workers = 1
accesslog = '-'
errorlog = '-'
#loglevel = 'debug'
access_log_format = '%({x-forwarded-for}i)s %(l)s %(t)s %(r)s %(s)s %(b)s %(f)s %(a)s'
bind = ['0.0.0.0:8080']
