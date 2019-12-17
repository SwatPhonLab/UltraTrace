from ... import utils

from . import OptionalWidget

class Spectrogram(OptionalWidget):
    def __init__(self):
        super().__init__()

        #if not args.spectrogram: # FIXME: allow passing command line arg to turn off spectrogram viewer
            #return

        try:
            self.is_imported = True
        except ImportError:
            utils.warn('Spectrogram Widget failed to load')
            return
