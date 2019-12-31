import pytest

from ..base import FileLoadError
from ..ogg import OggLoader


@pytest.mark.parametrize(
    "path", ["", "/path/to/nowhere", "/dev/null", "/etc/sudoers"],
)
def test_loading_from_invalid_file(path) -> None:
    with pytest.raises(FileLoadError):
        OggLoader.from_file(path)


@pytest.mark.parametrize(
    "path,duration_ms",
    [
        ("./test-data/example-audio/20110815035350_example.ogg", 6519),
        ("./test-data/example-audio/20110925121709_example.ogg", 10392),
        ("./test-data/example-audio/example.ogg", 6120),
        ("./test-data/example-audio/massenet_le_cid.ogg", 261078),
    ],
)
def test_loading_from_valid_file(path: str, duration_ms: int) -> None:
    ogg_file = OggLoader.from_file(path)
    assert len(ogg_file) == duration_ms
