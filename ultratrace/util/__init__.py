from .logging import *

__platform = None
def get_platform():
    # cache this result
    global __platform
    if __platform is None:
        try:
            import platform
            __platform = platform.system()
        except ImportError:
            __platform = 'generic'
        return __platform
    return __platform

def printProgressBar(iteration, total, prefix = '', suffix = '', decimals = 1, length = 25, fill = '█'):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = '\r')
    # Print New Line on Complete
    if iteration == total:
        print()

CROSSHAIR_SELECT_RADIUS = 9
CROSSHAIR_DRAG_BUFFER = 20

def decode_bytes(byt):
    for encoding in ['utf-8', 'Windows-1251', 'Windows-1252', 'ISO-8859-1']:
        try:
            return byt.decode(encoding)
        except UnicodeDecodeError:
            pass
    return ''
