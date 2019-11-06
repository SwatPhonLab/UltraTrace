import utils

from . import OptionalWidget

class Video(OptionalWidget):
    def __init__(self, app, args):
        super().__init__(app)

        if not args.video:
            return

        try:
            import threading
            import queue
            self.is_imported = True
        except ImportError:
            utils.warn('Video Widget failed to load')
            return
