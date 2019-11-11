import os
import PIL
import pydicom

from tqdm import tqdm

from .... import utils
from ..ADT import FileLoadError, TypedFile, TypedFileImpl

class ImageSet(TypedFile):

    class PNGSet(TypedFileImpl):
        mimetypes = ['image/png']
        extensions = ['.png']
        def load(self):
            raise NotImplementedError()

    class DICOM(TypedFileImpl):
        mimetypes = ['application/dicom']
        extensions = ['.dicom', '.dcm']

        def load(self):

            png_path = f'{self.path}-frames'

            if os.path.exists(png_path):
                print('exists!') # FIXME
                return

            try:
                dicom = pydicom.read_file(self.path)
            except pydicom.errors.InvalidDicomError as e:
                raise FileLoadError(str(e))

            pixels = dicom.pixel_array

            # check encoding, manipulate array if we need to
            if len(pixels.shape) == 3:
                is_greyscale = True
                frames, rows, columns = pixels.shape

            elif len(pixels.shape) == 4:
                # full-color RGB
                is_greyscale = False
                if pixels.shape[0] == 3:
                    # RGB-first
                    rgb, frames, rows, columns = pixels.shape
                    pixels.reshape( (frames, rows, columns, rgb) )
                elif pixels.shape[3] == 3:
                    # RGB-last
                    frames, rows, columns, rgb = pixels.shape
                else:
                    raise FileLoadError('Invalid DICOM ({self.path}), unknown shape {pixels.shape}')

            else:
                raise FileLoadError('Invalid DICOM ({self.path}), unknown shape {pixels.shape}')

            os.mkdir(png_path)
            for i in tqdm(range(frames), desc='converting to PNG'):
                filename = os.path.join(png_path, f'{i:06}.png')
                arr = pixels[ i,:,: ] if is_greyscale else pixels[ i,:,:,: ]
                img = PIL.Image.fromarray(arr)
                img.save(filename, format='PNG', compress_level=1)

        def convert_to_png(self, *args, **kwargs):
            print('converting')

    preferred_impls = [PNGSet, DICOM]

    def __init__(self):
        super().__init__()
