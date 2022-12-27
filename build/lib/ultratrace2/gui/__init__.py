import logging

from typing import Optional

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


logger = logging.getLogger(__name__)


class GUI(ThemedTk):
    def __init__(self, theme: Optional[str] = None):

        self.audio = Audio()
        self.control = Control()
        self.dicom = Dicom()
        self.spectrogram = Spectrogram()
        self.textgrid = TextGrid()
        self.trace = Trace()
        self.undo = Undo()
        self.video = Video()

        self.root = Container(
            ALIGN_VERTICAL,
            Container(
                ALIGN_HORIZONTAL,
                Container(ALIGN_VERTICAL, self.control, self.trace, self.undo,),
                self.dicom,
            ),
            Container(ALIGN_VERTICAL, self.spectrogram, self.textgrid,),
        )

        if hasattr(super(), "set_theme"):
            theme = get_theme(theme)
            if theme is not None:
                logger.info("Using TtkTheme: " + theme)
                super().__init__(theme=theme)
            else:
                super().__init__()
        else:
            super().__init__()
