import sys

def log(*msgs, **kwargs):
    print(*map(str, msgs), **kwargs, file=sys.stderr)

def debug(*msgs, **kwargs)
    log('DEBUG: ', *msgs, **kwargs)

def info(*msgs):
    log('INFO:  ', *msgs, **kwargs)

def warn(*msgs):
    log('WARN:  ', *msgs, **kwargs)

def error(*msgs):
    log('ERROR: ', *msgs, **kwargs)

def severe(*msgs):
    log('SEVERE:', *msgs, **kwargs)

__all__ = [ 'debug', 'info', 'warn', 'error', 'severe' ]
