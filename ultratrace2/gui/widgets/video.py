from ... import utils

from . import OptionalWidget

class Video(OptionalWidget):
    def __init__(self):
        super().__init__()

        #if not args.video: # FIXME: allow passing command line arg to turn off video viewer
            #return

        try:
            import threading
            import queue
            self.is_imported = True
        except ImportError:
            utils.warn('Video Widget failed to load')
            return
