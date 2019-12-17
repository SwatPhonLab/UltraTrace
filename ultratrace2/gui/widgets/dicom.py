from ... import utils

from . import OptionalWidget

class Dicom(OptionalWidget):
    def __init__(self):
        super().__init__()

        #if not args.dicom: # FIXME: allow passing command line arg to turn off DICOM viewer
            #return

        try:
            import numpy as np
            import pydicom as dicom # type: ignore
            from PIL import Image, ImageTk, ImageEnhance # type: ignore
            self.is_imported = True
        except ImportError:
            utils.warn('Dicom Widget failed to load')
            return
