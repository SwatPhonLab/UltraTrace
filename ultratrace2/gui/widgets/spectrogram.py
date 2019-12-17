from ... import utils

from . import OptionalWidget

class Spectrogram(OptionalWidget):
    def __init__(self, app):
        super().__init__(app)

        #if not args.spectrogram: # FIXME: allow passing command line arg to turn off spectrogram viewer
            #return

        try:
            self.is_imported = True
        except ImportError:
            utils.warn('Spectrogram Widget failed to load')
            return
