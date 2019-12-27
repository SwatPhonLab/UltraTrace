from PIL import Image, ImageFile  # type: ignore

import numpy as np
import os
import pydicom  # type: ignore

from .base import FileLoadError, ImageSetFileLoader


# PIL (via pydicom) will fail to load "truncated" images sometimes, so we need to tell it to
# ignore these.  For context, see https://github.com/python-pillow/Pillow/issues/1510
ImageFile.LOAD_TRUNCATED_IMAGES = True


class DICOMLoader(ImageSetFileLoader):
    def get_path(self) -> str:
        return self._path

    def set_path(self, path) -> None:
        self._path = path

    def __init__(self, path: str, pixels: np.ndarray):
        """Construct the DICOMLoader from a pixel array.

        The `shape` of the pixel array should be `(n_frames, n_rows, n_columns)` for greyscale
        images and `(n_frames, n_rows, n_columns, rgb_data)` for full-color images."""
        self.set_path(path)
        self.pixels = pixels
        # FIXME: these should be in the `.ultratrace/` dir
        self.png_dir = f"{path}-frames"
        if not os.path.exists(self.png_dir):
            os.mkdir(self.png_dir, mode=0o755)

    def is_greyscale(self) -> bool:
        return len(self.pixels.shape) == 3

    def __len__(self) -> int:
        return self.pixels.shape[0]

    def get_height(self) -> int:
        return self.pixels.shape[1]

    def get_width(self) -> int:
        return self.pixels.shape[2]

    def get_png_filepath_for_frame(self, i: int) -> str:
        return os.path.join(self.png_dir, f"{i:06}.png")

    def get_frame(self, i: int) -> Image.Image:
        png_filepath = self.get_png_filepath_for_frame(i)
        if os.path.exists(png_filepath):
            return Image.open(png_filepath)
        else:
            arr = (
                self.pixels[i, :, :] if self.is_greyscale() else self.pixels[i, :, :, :]
            )
            img = Image.fromarray(arr)
            img.save(png_filepath, format="PNG", compress_level=1)
            return img

    @classmethod
    def from_file(cls, path: str) -> "DICOMLoader":
        try:

            if not os.path.exists(path):
                raise FileNotFoundError(f"Cannot load from path: '{path}'")

            dicom = pydicom.read_file(path)

            pixels: np.ndarray = dicom.pixel_array

            if len(pixels.shape) == 2:
                # For DICOM consisting of a single frame, we need to add a singleton axis.
                pixels = np.expand_dims(pixels, axis=0)
                return cls(path, pixels)

            elif len(pixels.shape) == 3:
                n_frames, n_rows, n_columns = pixels.shape
                return cls(path, pixels)

            elif len(pixels.shape) == 4:
                # full-color RGB
                if pixels.shape[0] == 3:
                    # RGB-first
                    rgb, n_frames, n_rows, n_columns = pixels.shape
                    pixels.reshape((n_frames, n_rows, n_columns, rgb))
                    return cls(path, pixels)

                elif pixels.shape[3] == 3:
                    # RGB-last
                    n_frames, n_rows, n_columns, rgb = pixels.shape
                    return cls(path, pixels)

            raise ValueError(f"Invalid DICOM ({path}), unknown shape {pixels.shape}")

        except Exception as e:
            raise FileLoadError(
                f"Invalid DICOM ({path}), unable to read: {str(e)}"
            ) from e

    def convert_to_png(self, *args, **kwargs):
        # FIXME: implement this as a helper function
        raise NotImplementedError()
