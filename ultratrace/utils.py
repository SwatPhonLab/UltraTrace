import sys

def log(level, *msgs):
    print(level + ': ', ' '.join(map(str, msgs)), file=sys.stderr)

def severe(*msgs):
    log('SEVERE', *msgs)

def error(*msgs):
    log('ERROR', *msgs)

def warn(*msgs):
    log('WARN', *msgs)

def info(*msgs):
    log('INFO', *msgs)

def debug(*msgs):
    log('DEBUG', *msgs)
