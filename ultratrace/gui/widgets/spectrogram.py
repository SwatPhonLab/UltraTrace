import utils

from . import OptionalWidget

class Spectrogram(OptionalWidget):
    def __init__(self, app, args):
        super().__init__(app)

        if not args.spectrogram:
            return

        try:
            self.is_imported = True
        except ImportError:
            utils.warn('Spectrogram Widget failed to load')
            return
