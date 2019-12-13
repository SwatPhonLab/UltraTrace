from ... import utils

from . import OptionalWidget

class Dicom(OptionalWidget):
    def __init__(self, app):
        super().__init__(app)

        if not args.dicom:
            return

        try:
            import numpy as np
            import pydicom as dicom
            from PIL import Image, ImageTk, ImageEnhance
            self.is_imported = True
        except ImportError:
            utils.warn('Dicom Widget failed to load')
            return
