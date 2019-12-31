import pytest

from ..base import FileLoadError
from ..mp3 import MP3Loader


@pytest.mark.parametrize(
    "path", ["", "/path/to/nowhere", "/dev/null", "/etc/sudoers"],
)
def test_loading_from_invalid_file(path) -> None:
    with pytest.raises(FileLoadError):
        MP3Loader.from_file(path)


@pytest.mark.parametrize(
    "path,duration_ms",
    [
        ("./test-data/example-audio/bachfugue.mp3", 39552),
        ("./test-data/example-audio/cello82.mp3", 14160),
        ("./test-data/example-audio/gtr-nylon22.mp3", 5068),
        ("./test-data/example-audio/harpsi-cs.mp3", 18912),
        ("./test-data/example-audio/pno-cs.mp3", 20064),
    ],
)
def test_loading_from_valid_file(path: str, duration_ms: int) -> None:
    mp3_file = MP3Loader.from_file(path)
    assert len(mp3_file) == duration_ms
