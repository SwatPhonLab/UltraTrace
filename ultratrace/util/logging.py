import sys

def log(*msgs, **kwargs):
    print(*map(str, msgs), **kwargs, file=sys.stderr)

def debug(*msgs, **kwargs):
    log('DEBUG: ', *msgs, **kwargs)

def info(*msgs, **kwargs):
    log('INFO:  ', *msgs, **kwargs)

def warn(*msgs, **kwargs):
    log('WARN:  ', *msgs, **kwargs)

def error(*msgs, **kwargs):
    log('ERROR: ', *msgs, **kwargs)

def severe(*msgs, **kwargs):
    log('SEVERE:', *msgs, **kwargs)

__all__ = [ 'debug', 'info', 'warn', 'error', 'severe' ]
