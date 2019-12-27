import pytest

from ..base import FileLoadError
from ..textgrid import TextGridLoader


@pytest.mark.parametrize(
    "path", ["", "/path/to/nowhere", "/dev/null", "/etc/sudoers"],
)
def test_loading_from_invalid_file(path) -> None:
    with pytest.raises(FileLoadError):
        TextGridLoader.from_file(path)


@pytest.mark.parametrize(
    "path",
    [
        "test-data/qumuq/File049.TextGrid",
        "test-data/qumuq/File059.TextGrid",
        "test-data/qumuq/File005.TextGrid",
        "test-data/qumuq/File043.TextGrid",
        "test-data/qumuq/File020.TextGrid",
        "test-data/qumuq/File042.TextGrid",
        "test-data/qumuq/File012.TextGrid",
        "test-data/qumuq/File037.TextGrid",
        "test-data/qumuq/File056.TextGrid",
        "test-data/qumuq/File062.TextGrid",
        "test-data/qumuq/File004.TextGrid",
        "test-data/qumuq/File044.TextGrid",
        "test-data/qumuq/File038.TextGrid",
        "test-data/qumuq/File045.TextGrid",
        "test-data/qumuq/File008.TextGrid",
        "test-data/qumuq/File007.TextGrid",
        "test-data/qumuq/File067.TextGrid",
        "test-data/qumuq/File031.TextGrid",
        "test-data/qumuq/File030.TextGrid",
        "test-data/qumuq/File064.TextGrid",
        "test-data/qumuq/File046.TextGrid",
        "test-data/qumuq/File054.TextGrid",
        "test-data/qumuq/File001.TextGrid",
        "test-data/qumuq/File017.TextGrid",
        "test-data/qumuq/File039.TextGrid",
        "test-data/qumuq/File053.TextGrid",
        "test-data/qumuq/File060.TextGrid",
        "test-data/qumuq/File025.TextGrid",
        "test-data/qumuq/File034.TextGrid",
        "test-data/qumuq/File050.TextGrid",
        "test-data/qumuq/File035.TextGrid",
        "test-data/qumuq/File055.TextGrid",
        "test-data/qumuq/File051.TextGrid",
        "test-data/qumuq/File021.TextGrid",
        "test-data/qumuq/File040.TextGrid",
        "test-data/qumuq/File016.TextGrid",
        "test-data/qumuq/File058.TextGrid",
        "test-data/qumuq/File006.TextGrid",
        "test-data/qumuq/File052.TextGrid",
        "test-data/qumuq/File018.TextGrid",
        "test-data/qumuq/File061.TextGrid",
        "test-data/qumuq/File013.TextGrid",
        "test-data/qumuq/File033.TextGrid",
        "test-data/qumuq/File041.TextGrid",
        "test-data/qumuq/File026.TextGrid",
        "test-data/qumuq/File014.TextGrid",
        "test-data/qumuq/File010.TextGrid",
        "test-data/qumuq/File063.TextGrid",
        "test-data/qumuq/File023.TextGrid",
        "test-data/qumuq/File011.TextGrid",
        "test-data/qumuq/File002.TextGrid",
        "test-data/qumuq/File066.TextGrid",
        "test-data/qumuq/File009.TextGrid",
        "test-data/qumuq/File003.TextGrid",
        "test-data/qumuq/File068.TextGrid",
        "test-data/qumuq/File048.TextGrid",
        "test-data/qumuq/File036.TextGrid",
        "test-data/qumuq/File032.TextGrid",
        "test-data/qumuq/File028.TextGrid",
        "test-data/qumuq/File057.TextGrid",
        "test-data/qumuq/File015.TextGrid",
        "test-data/qumuq/File027.TextGrid",
        "test-data/qumuq/File024.TextGrid",
        "test-data/qumuq/File065.TextGrid",
        "test-data/qumuq/File029.TextGrid",
        "test-data/qumuq/File022.TextGrid",
        "test-data/qumuq/File047.TextGrid",
        "test-data/qumuq/File019.TextGrid",
        "test-data/ftyers/20150629171639.TextGrid",
    ],
)
def test_loading_from_valid_file(path) -> None:
    loaded_file = TextGridLoader.from_file(path)
    assert isinstance(loaded_file, TextGridLoader)
