import logging

from . import OptionalWidget


class Dicom(OptionalWidget):
    def __init__(self):
        super().__init__()

        # FIXME: allow passing command line arg to turn off DICOM viewer

        try:
            import numpy as np # noqa: F401
            import pydicom as dicom # type: ignore # noqa: F401
            from PIL import Image, ImageTk, ImageEnhance # type: ignore # noqa: F401
            self.is_imported = True
        except ImportError:
            logging.warning('Dicom Widget failed to load')
            return
