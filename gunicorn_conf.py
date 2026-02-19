import multiprocessing

workers = int(multiprocessing.cpu_count() / 2) or 1
bind = '0.0.0.0:5001'
worker_class = 'eventlet'
timeout = 30
