from typing import Type
import logging


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
    def __init__(self, app: Type['App'], theme: str = None):

        self.app = app

        self.audio = Audio(app)
        self.control = Control(app)
        self.dicom = Dicom(app)
        self.spectrogram = Spectrogram(app)
        self.textgrid = TextGrid(app)
        self.trace = Trace(app)
        self.undo = Undo(app)
        self.video = Video(app)

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
            theme = get_theme(theme)
            if theme is not None:
                logging.info('Using TtkTheme: ' + theme)
                super().__init__(theme=theme)
            else:
                super().__init__()
        else:
            super().__init__()
