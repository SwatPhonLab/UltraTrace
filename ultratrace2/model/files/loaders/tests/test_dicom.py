from PIL import Image  # type: ignore

import pytest

from ..dicom import DICOMLoader
from ..base import FileLoadError


@pytest.mark.parametrize(
    "path", ["", "/path/to/nowhere", "/dev/null", "/etc/sudoers"],
)
def test_loading_from_invalid_file(path) -> None:
    with pytest.raises(FileLoadError):
        DICOMLoader.from_file(path)


@pytest.mark.parametrize(
    "path,n_frames,height,width,is_greyscale",
    [
        ("./test-data/example-dicom/0002.DCM", 96, 512, 512, True),
        ("./test-data/example-dicom/0003.DCM", 17, 512, 512, True),
        ("./test-data/example-dicom/0004.DCM", 17, 512, 512, True),
        ("./test-data/example-dicom/0009.DCM", 137, 512, 512, True),
        ("./test-data/example-dicom/0012.DCM", 70, 512, 512, True),
        ("./test-data/example-dicom/0015.DCM", 1, 1024, 1024, True),
        # FIXME: The `0020.DCM` file is not getting parsed correctly by pydicom -- it is a
        #        full-color image, using PALETTE COLOR and not RGB channel of pixel_array.
        #        This is probably something we should fix eventually!  Looks like there's
        #        some preliminary work [here](https://github.com/pydicom/pydicom/issues/205),
        #        although I haven't dug too deeply.
        ("./test-data/example-dicom/0020.DCM", 11, 430, 600, True),
        ("./test-data/example-dicom/MRBRAIN.DCM", 1, 512, 512, True),
        ("./test-data/example-dicom/bmode.dcm", 37, 768, 1024, False),
    ],
)
def test_loading_from_valid_file(path, n_frames, height, width, is_greyscale) -> None:
    loader = DICOMLoader.from_file(path)
    assert loader.get_path() == path
    assert len(loader) == n_frames
    assert loader.get_height() == height
    assert loader.get_width() == width
    assert loader.is_greyscale() == is_greyscale
    assert isinstance(loader.get_frame(0), Image.Image)
