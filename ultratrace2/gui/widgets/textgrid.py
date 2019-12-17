import logging

from . import OptionalWidget


class TextGrid(OptionalWidget):
    def __init__(self):
        super().__init__()

        # FIXME: allow passing command line arg to turn off textgrid viewer

        try:
            from textgrid import TextGrid # type: ignore # noqa: F401
            self.is_imported = True
        except ImportError:
            logging.warning('TextGrid Widget failed to load')
            return
