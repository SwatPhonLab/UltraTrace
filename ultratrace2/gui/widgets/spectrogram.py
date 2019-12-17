import logging

from . import OptionalWidget


logger = logging.getLogger(__name__)


class Spectrogram(OptionalWidget):
    def __init__(self):
        super().__init__()

        # FIXME: allow passing command line arg to turn off spectrogram viewer

        try:
            self.is_imported = True
        except ImportError:
            logger.warning("Spectrogram Widget failed to load")
            return
