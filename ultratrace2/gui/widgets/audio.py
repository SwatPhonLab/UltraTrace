import logging

from . import OptionalWidget


logger = logging.getLogger(__name__)


class Audio(OptionalWidget):
    def __init__(self):
        super().__init__()

        # FIXME: allow disabling of widgets via command line args

        try:
            import pyaudio  # type: ignore # noqa: F401
            from pydub import AudioSegment  # type: ignore # noqa: F401

            self.is_imported = True
        except ImportError:
            logger.warning("Audio Widget failed to load")
            return
