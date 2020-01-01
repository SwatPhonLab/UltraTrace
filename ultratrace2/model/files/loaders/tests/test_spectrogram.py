import os
import PIL  # type: ignore
import pytest

from ..base import SoundFileLoader
from ..mp3 import MP3Loader


@pytest.mark.parametrize(
    "loader, path",
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
def test_interpreting_as_image(loader: SoundFileLoader, path: str) -> None:
    loaded_file = loader.from_file(path)
    spec_arr = loaded_file.get_spectrogram(
        start_time_ms=0,
        stop_time_ms=len(loaded_file),
        window_length=0.005,
        max_frequency=5000,
        dynamic_range=90,
        n_slices=10 ** 7,
    )
    assert spec_arr is not None
    im = PIL.Image.fromarray(spec_arr).convert("RGB").resize((800, 600))
    im.save("/tmp/" + os.path.basename(path) + ".png")
