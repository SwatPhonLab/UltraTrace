from typing import Sequence

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
    "path,tier_names,start_time,end_time",
    [
        (
            "./test-data/ftyers/20150629171639.TextGrid",
            [
                "sentence",
                "word",
                "orthographic vowel",
                "all frames",
                "all frames",
                "all frames.original",
            ],
            0.0,
            28.2,
        ),
        ("./test-data/qumuq/File001.TextGrid", ["annotation_0"], 0.0, 6.17651),
        ("./test-data/qumuq/File002.TextGrid", ["annotation_0"], 0.0, 3.65714),
        ("./test-data/qumuq/File003.TextGrid", ["annotation_0"], 0.0, 4.52789),
        ("./test-data/qumuq/File004.TextGrid", ["annotation_0"], 0.0, 4.58594),
        ("./test-data/qumuq/File005.TextGrid", ["annotation_0"], 0.0, 3.52943),
        ("./test-data/qumuq/File006.TextGrid", ["annotation_0"], 0.0, 3.86612),
        ("./test-data/qumuq/File007.TextGrid", ["annotation_0"], 0.0, 3.99383),
        ("./test-data/qumuq/File008.TextGrid", ["annotation_0"], 0.0, 3.87773),
        ("./test-data/qumuq/File009.TextGrid", ["annotation_0"], 0.0, 3.58748),
        ("./test-data/qumuq/File010.TextGrid", ["annotation_0"], 0.0, 4.48145),
        ("./test-data/qumuq/File011.TextGrid", ["annotation_0"], 0.0, 3.87773),
        ("./test-data/qumuq/File012.TextGrid", ["annotation_0"], 0.0, 3.78485),
        ("./test-data/qumuq/File013.TextGrid", ["annotation_0"], 0.0, 4.16798),
        ("./test-data/qumuq/File014.TextGrid", ["annotation_0"], 0.0, 4.00544),
        ("./test-data/qumuq/File015.TextGrid", ["annotation_0"], 0.0, 3.91256),
        ("./test-data/qumuq/File016.TextGrid", ["annotation_0"], 0.0, 4.28408),
        ("./test-data/qumuq/File017.TextGrid", ["annotation_0"], 0.0, 4.31891),
        (
            "./test-data/qumuq/File018.TextGrid",
            ["annotation_0", "annotation_1"],
            0.0,
            4.04027,
        ),
        ("./test-data/qumuq/File019.TextGrid", ["annotation_0"], 0.0, 4.06349),
        ("./test-data/qumuq/File020.TextGrid", ["annotation_0"], 0.0, 4.04027),
        ("./test-data/qumuq/File021.TextGrid", ["annotation_0"], 0.0, 3.98222),
        ("./test-data/qumuq/File022.TextGrid", ["annotation_0"], 0.0, 4.09832),
        ("./test-data/qumuq/File023.TextGrid", ["annotation_0"], 0.0, 4.24925),
        ("./test-data/qumuq/File024.TextGrid", ["annotation_0"], 0.0, 4.04027),
        ("./test-data/qumuq/File025.TextGrid", ["annotation_0"], 0.0, 4.05188),
        ("./test-data/qumuq/File026.TextGrid", ["annotation_0"], 0.0, 4.82975),
        ("./test-data/qumuq/File027.TextGrid", ["annotation_0"], 0.0, 4.69043),
        ("./test-data/qumuq/File028.TextGrid", ["annotation_0"], 0.0, 4.51628),
        ("./test-data/qumuq/File029.TextGrid", ["annotation_0"], 0.0, 4.45823),
        ("./test-data/qumuq/File030.TextGrid", ["annotation_0"], 0.0, 3.92417),
        ("./test-data/qumuq/File031.TextGrid", ["annotation_0"], 0.0, 4.17959),
        ("./test-data/qumuq/File032.TextGrid", ["annotation_0"], 0.0, 4.52789),
        ("./test-data/qumuq/File033.TextGrid", ["annotation_0"], 0.0, 4.15637),
        ("./test-data/qumuq/File034.TextGrid", ["annotation_0"], 0.0, 4.79492),
        (
            "./test-data/qumuq/File035.TextGrid",
            ["annotation_0", "PointTier_0"],
            0.0,
            2.70512,
        ),
        ("./test-data/qumuq/File036.TextGrid", ["annotation_0"], 0.0, 2.73995),
        ("./test-data/qumuq/File037.TextGrid", ["annotation_0"], 0.0, 3.00698),
        ("./test-data/qumuq/File038.TextGrid", ["annotation_0"], 0.0, 2.93732),
        ("./test-data/qumuq/File039.TextGrid", ["annotation_0"], 0.0, 3.00698),
        ("./test-data/qumuq/File040.TextGrid", ["annotation_0"], 0.0, 3.00698),
        ("./test-data/qumuq/File041.TextGrid", ["annotation_0"], 0.0, 3.28562),
        (
            "./test-data/qumuq/File042.TextGrid",
            ["annotation_0", "annotation_1"],
            0.0,
            3.04181,
        ),
        ("./test-data/qumuq/File043.TextGrid", ["annotation_0"], 0.0, 2.75156),
        ("./test-data/qumuq/File044.TextGrid", ["annotation_0"], 0.0, 3.20435),
        ("./test-data/qumuq/File045.TextGrid", ["annotation_0"], 0.0, 2.53098),
        ("./test-data/qumuq/File046.TextGrid", ["annotation_0"], 0.0, 3.01859),
        ("./test-data/qumuq/File047.TextGrid", ["annotation_0"], 0.0, 2.78639),
        ("./test-data/qumuq/File048.TextGrid", ["annotation_0"], 0.0, 3.06503),
        ("./test-data/qumuq/File049.TextGrid", ["annotation_0"], 0.0, 3.16635),
        ("./test-data/qumuq/File050.TextGrid", ["annotation_0"], 0.0, 2.93732),
        ("./test-data/qumuq/File051.TextGrid", ["annotation_0"], 0.0, 3.15791),
        ("./test-data/qumuq/File052.TextGrid", ["annotation_0"], 0.0, 3.05342),
        ("./test-data/qumuq/File053.TextGrid", ["annotation_0"], 0.0, 3.58748),
        ("./test-data/qumuq/File054.TextGrid", ["annotation_0"], 0.0, 3.76163),
        ("./test-data/qumuq/File055.TextGrid", ["annotation_0"], 0.0, 2.82122),
        ("./test-data/qumuq/File056.TextGrid", ["annotation_0"], 0.0, 3.12308),
        ("./test-data/qumuq/File057.TextGrid", ["annotation_0"], 0.0, 2.9141),
        ("./test-data/qumuq/File058.TextGrid", ["annotation_0"], 0.0, 2.70512),
        ("./test-data/qumuq/File059.TextGrid", ["annotation_0"], 0.0, 2.76317),
        ("./test-data/qumuq/File060.TextGrid", ["annotation_0"], 0.0, 3.1463),
        ("./test-data/qumuq/File061.TextGrid", ["annotation_0"], 0.0, 3.23918),
        ("./test-data/qumuq/File062.TextGrid", ["annotation_0"], 0.0, 3.25079),
        ("./test-data/qumuq/File063.TextGrid", ["annotation_0"], 0.0, 3.06503),
        ("./test-data/qumuq/File064.TextGrid", ["annotation_0"], 0.0, 3.23918),
        ("./test-data/qumuq/File065.TextGrid", ["annotation_0"], 0.0, 3.00698),
        ("./test-data/qumuq/File066.TextGrid", ["annotation_0"], 0.0, 3.01859),
        ("./test-data/qumuq/File067.TextGrid", ["annotation_0"], 0.0, 3.06503),
    ],
)
def test_loading_from_valid_file(
    path: str, tier_names: Sequence[str], start_time: float, end_time: float
) -> None:
    loaded_file = TextGridLoader.from_file(path)
    assert isinstance(loaded_file, TextGridLoader)
    assert len(loaded_file.get_tier_names()) == len(tier_names)
    for actual_tier_name, expected_tier_name in zip(
        loaded_file.get_tier_names(), tier_names
    ):
        assert actual_tier_name == expected_tier_name
    assert loaded_file.get_start() == start_time
    assert loaded_file.get_end() == end_time
    offset = 3.1415
    loaded_file.set_offset(offset)
    assert loaded_file.get_start() == start_time + offset
    assert loaded_file.get_end() == end_time + offset
