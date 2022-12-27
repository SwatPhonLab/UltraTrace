import logging

from . import OptionalWidget


logger = logging.getLogger(__name__)


class Video(OptionalWidget):
    def __init__(self):
        super().__init__()

        # FIXME: allow passing command line arg to turn off video viewer

        try:
            import threading  # noqa: F401
            import queue  # noqa: F401

            self.is_imported = True
        except ImportError:
            logger.warning("Video Widget failed to load")
            return
