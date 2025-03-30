import os
import PIL  # type: ignore
import pytest

from ..base import SoundFileLoader
from ..mp3 import MP3Loader
from ..parselmouth_spectrogram import ParselmouthLoader


@pytest.mark.parametrize(
    "sound_file_loader, path",
    [
        (MP3Loader, "./test-data/example-audio/cello82.mp3"),
        (MP3Loader, "./test-data/example-audio/harpsi-cs.mp3"),
        (MP3Loader, "./test-data/example-audio/gtr-nylon22.mp3"),
        (MP3Loader, "./test-data/example-audio/pno-cs.mp3"),
        (MP3Loader, "./test-data/example-audio/bachfugue.mp3"),
        (MP3Loader, "./test-data/example-bundles/ex016/link00.mp3"),
        (MP3Loader, "./test-data/example-bundles/ex003/file01.mp3"),
        (MP3Loader, "./test-data/example-bundles/ex004/file00.mp3"),
        (MP3Loader, "./test-data/example-bundles/ex002/file00.mp3"),
        (MP3Loader, "./test-data/example-bundles/ex015/file00.mp3"),
        (
            MP3Loader,
            "./test-data/example-bundles/ex012/sub01/sub00/sub00/sub00/file00.mp3",
        ),
        (MP3Loader, "./test-data/example-bundles/ex009/file00.mp3"),
        (MP3Loader, "./test-data/example-bundles/ex008/file01.mp3"),
        (MP3Loader, "./test-data/example-bundles/ex008/file00.mp3"),
        (MP3Loader, "./test-data/example-bundles/ex008/file02.mp3"),
    ],
)
def test_loading_from_sound_file(sound_file_loader: SoundFileLoader, path: str) -> None:
    try:
        expected_pm_path = path + ".pmpkl"
        assert not os.path.exists(expected_pm_path)
        sound_file = sound_file_loader.from_file(path)
        pm_file = ParselmouthLoader.from_sound_file(sound_file)
        assert isinstance(pm_file, ParselmouthLoader)
        assert pm_file.get_path() == expected_pm_path
        assert os.path.exists(expected_pm_path)
    finally:
        if os.path.exists(expected_pm_path):
            os.remove(expected_pm_path)


@pytest.mark.parametrize(
    "path",
    [
        "./test-data/example-parselmouth/00.pmpkl",
        "./test-data/example-parselmouth/01.pmpkl",
        "./test-data/example-parselmouth/02.pmpkl",
        "./test-data/example-parselmouth/03.pmpkl",
        "./test-data/example-parselmouth/04.pmpkl",
        "./test-data/example-parselmouth/05.pmpkl",
        "./test-data/example-parselmouth/06.pmpkl",
        "./test-data/example-parselmouth/07.pmpkl",
        "./test-data/example-parselmouth/08.pmpkl",
        "./test-data/example-parselmouth/09.pmpkl",
        "./test-data/example-parselmouth/10.pmpkl",
        "./test-data/example-parselmouth/11.pmpkl",
        "./test-data/example-parselmouth/12.pmpkl",
        "./test-data/example-parselmouth/13.pmpkl",
        "./test-data/example-parselmouth/14.pmpkl",
    ],
)
def test_loading_from_pmpkl_file(path: str) -> None:
    pm_file = ParselmouthLoader.from_file(path)
    assert isinstance(pm_file, ParselmouthLoader)
    im = pm_file.get_image(
        start_time_ms=0,
        stop_time_ms=10,
        window_length=0.005,
        max_frequency=5000,
        dynamic_range=90,
        n_slices=10 ** 7,
    )
    assert isinstance(im, PIL.Image.Image)
