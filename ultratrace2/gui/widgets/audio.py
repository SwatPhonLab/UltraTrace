from ... import utils

from . import OptionalWidget

class Audio(OptionalWidget):
    def __init__(self):
        super().__init__()

        #if not args.audio: # FIXME: allow disabling of widgets via command line args
            #return

        try:
            import pyaudio # type: ignore
            from pydub import AudioSegment # type: ignore
            self.is_imported = True
        except ImportError:
            utils.warn('Audio Widget failed to load')
            return
