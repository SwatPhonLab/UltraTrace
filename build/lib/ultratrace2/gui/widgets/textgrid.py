import logging

from . import OptionalWidget


logger = logging.getLogger(__name__)


class TextGrid(OptionalWidget):
    def __init__(self):
        super().__init__()

        # FIXME: allow passing command line arg to turn off textgrid viewer

        try:
            from textgrid import TextGrid  # type: ignore # noqa: F401

            self.is_imported = True
        except ImportError:
            logger.warning("TextGrid Widget failed to load")
            return
