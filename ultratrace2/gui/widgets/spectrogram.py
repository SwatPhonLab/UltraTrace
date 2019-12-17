import logging

from . import OptionalWidget


class Spectrogram(OptionalWidget):
    def __init__(self):
        super().__init__()

        # FIXME: allow passing command line arg to turn off spectrogram viewer

        try:
            self.is_imported = True
        except ImportError:
            logging.warning('Spectrogram Widget failed to load')
            return
