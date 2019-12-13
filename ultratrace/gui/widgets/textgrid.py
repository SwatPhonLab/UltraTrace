from ... import utils

from . import OptionalWidget

class TextGrid(OptionalWidget):
    def __init__(self, app, args):
        super().__init__(app)

        if not args.textgrid:
            return

        try:
            from textgrid import TextGrid
            self.is_imported = True
        except ImportError:
            utils.warn('TextGrid Widget failed to load')
            return
