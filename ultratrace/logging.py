import sys

def log(*msgs):
    print(*msgs, file=sys.stderr)

def debug(*msgs):
    log('DEBUG:', *msgs)

def info(*msgs):
    log('INFO:', *msgs)

def warn(*msgs):
    log('WARN:', *msgs)

def error(*msgs):
    log('ERROR:', *msgs)

def severe(*msgs):
    log('SEVERE:', *msgs)

__all__ = [ 'debug', 'info', 'warn', 'error', 'severe' ]
