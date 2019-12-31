import pytest

from ..base import FileLoadError
from ..flac import FLACLoader


@pytest.mark.parametrize(
    "path", ["", "/path/to/nowhere", "/dev/null", "/etc/sudoers"],
)
def test_loading_from_invalid_file(path) -> None:
    with pytest.raises(FileLoadError):
        FLACLoader.from_file(path)


@pytest.mark.parametrize(
    "path,duration_ms",
    [
        ("./test-data/example-audio/2L-125_04_stereo.mqa.flac", 97760),
        ("./test-data/example-audio/2L-125_stereo-176k-24b_04.flac", 97760),
        ("./test-data/example-audio/2L-125_stereo-44k-16b_04.flac", 97760),
        ("./test-data/example-audio/2L-125_stereo-88k-24b_04.flac", 97760),
        ("./test-data/ftyers/20150629171639.flac", 28200),
    ],
)
def test_loading_from_valid_file(path: str, duration_ms: int) -> None:
    flac_file = FLACLoader.from_file(path)
    assert len(flac_file) == duration_ms
