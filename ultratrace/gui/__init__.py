from .. import utils

from .themes import ThemedTk, get_theme
from .widgets import ALIGN_HORIZONTAL, ALIGN_VERTICAL
from .widgets.audio import Audio
from .widgets.container import Container
from .widgets.control import Control
from .widgets.dicom import Dicom
from .widgets.spectrogram import Spectrogram
from .widgets.textgrid import TextGrid
from .widgets.trace import Trace
from .widgets.undo import Undo
from .widgets.video import Video

class GUI(ThemedTk):
    def __init__(self, app, args):

        self.app = app

        self.audio = Audio(app, args)
        self.control = Control(app, args)
        self.dicom = Dicom(app, args)
        self.spectrogram = Spectrogram(app, args)
        self.textgrid = TextGrid(app, args)
        self.trace = Trace(app, args)
        self.undo = Undo(app, args)
        self.video = Video(app, args)

        self.root = Container(app, ALIGN_VERTICAL,
            Container(app, ALIGN_HORIZONTAL,
                Container(app, ALIGN_VERTICAL,
                    self.control,
                    self.trace,
                    self.undo,
                ),
                self.dicom,
            ),
            Container(app, ALIGN_VERTICAL,
                self.spectrogram,
                self.textgrid,
            ),
        )

        if hasattr(super(), 'set_theme'):
            theme = get_theme(args.theme)
            if theme is not None:
                utils.info('Using TtkTheme: ' + theme)
                super().__init__(theme=theme)
            else:
                super().__init__()
        else:
            super().__init__()
