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
