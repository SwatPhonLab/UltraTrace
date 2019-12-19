import numpy as np
import os
import PIL  # type: ignore
import pydicom  # type: ignore

from tqdm import tqdm  # type: ignore

from ..adt import FileLoadError, TypedFile


class DICOM(TypedFile):

    mimetypes = ["application/dicom"]
    extensions = [".dicom", ".dcm"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # FIXME: make this more granular
        self.png_path = f"{self.path}-frames"

    def load(self) -> None:
        if os.path.exists(self.png_path):
            return

        try:
            dicom = pydicom.read_file(self.path)
        except pydicom.errors.InvalidDicomError as e:
            raise FileLoadError(str(e))

        pixels: np.ndarray = dicom.pixel_array

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
                pixels.reshape((frames, rows, columns, rgb))
            elif pixels.shape[3] == 3:
                # RGB-last
                frames, rows, columns, rgb = pixels.shape
            else:
                raise FileLoadError(
                    "Invalid DICOM ({self.path}), unknown shape {pixels.shape}"
                )

        else:
            raise FileLoadError(
                "Invalid DICOM ({self.path}), unknown shape {pixels.shape}"
            )

        os.mkdir(self.png_path, mode=0o755)
        for i in tqdm(range(frames), desc="converting to PNG"):
            filename = os.path.join(self.png_path, f"{i:06}.png")
            arr = pixels[i, :, :] if is_greyscale else pixels[i, :, :, :]
            img = PIL.Image.fromarray(arr)
            img.save(filename, format="PNG", compress_level=1)

    def convert_to_png(self, *args, **kwargs):
        # FIXME: implement this function, signatures, etc.
        print("converting")
