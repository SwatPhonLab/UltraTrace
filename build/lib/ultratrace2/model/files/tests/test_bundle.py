from typing import Dict, Mapping, Sequence, Tuple, Type

import os
import pytest

from ..bundle import FileBundle, FileBundleList
from ..loaders import DICOMLoader, FLACLoader, MP3Loader, TextGridLoader, WAVLoader
from ..loaders.base import (
    FileLoaderBase,
    AlignmentFileLoader,
    ImageSetFileLoader,
    SoundFileLoader,
)


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(),
        dict(alignment_file=None),
        dict(image_set_file=None),
        dict(sound_file=None),
        dict(alignment_file=None, image_set_file=None),
        dict(alignment_file=None, sound_file=None),
        dict(image_set_file=None, sound_file=None),
        dict(alignment_file=None, image_set_file=None, sound_file=None),
    ],
)
def test_empty_file_bundle_constructor(kwargs: Mapping[str, None]) -> None:
    fb = FileBundle("test", **kwargs)
    assert not fb.has_impl()
    assert str(fb) == 'Bundle("test",None,None,None)'


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(
            alignment_file=TextGridLoader.from_file(
                "./test-data/example-bundles/ex000/file00.TextGrid"
            )
        ),
        dict(
            image_set_file=DICOMLoader.from_file(
                "./test-data/example-bundles/ex004/file00.dicom"
            )
        ),
        dict(
            sound_file=MP3Loader.from_file(
                "./test-data/example-bundles/ex002/file00.mp3"
            )
        ),
        dict(
            alignment_file=TextGridLoader.from_file(
                "./test-data/example-bundles/ex000/file00.TextGrid"
            ),
            image_set_file=DICOMLoader.from_file(
                "./test-data/example-bundles/ex004/file00.dicom"
            ),
        ),
        dict(
            alignment_file=TextGridLoader.from_file(
                "./test-data/example-bundles/ex000/file00.TextGrid"
            ),
            sound_file=MP3Loader.from_file(
                "./test-data/example-bundles/ex002/file00.mp3"
            ),
        ),
        dict(
            image_set_file=DICOMLoader.from_file(
                "./test-data/example-bundles/ex004/file00.dicom"
            ),
            sound_file=MP3Loader.from_file(
                "./test-data/example-bundles/ex002/file00.mp3"
            ),
        ),
        dict(
            alignment_file=TextGridLoader.from_file(
                "./test-data/example-bundles/ex000/file00.TextGrid"
            ),
            image_set_file=DICOMLoader.from_file(
                "./test-data/example-bundles/ex004/file00.dicom"
            ),
            sound_file=MP3Loader.from_file(
                "./test-data/example-bundles/ex002/file00.mp3"
            ),
        ),
    ],
)
def test_file_bundle_constructor(kwargs: Mapping[str, FileLoaderBase]) -> None:
    fb = FileBundle("test", **kwargs)
    assert fb.has_impl()
    if "alignment_file" in kwargs:
        alignment_file = fb.get_alignment_file()
        assert isinstance(alignment_file, AlignmentFileLoader)
        assert alignment_file.get_path() == kwargs["alignment_file"].get_path()
    if "image_set_file" in kwargs:
        image_set_file = fb.get_image_set_file()
        assert isinstance(image_set_file, ImageSetFileLoader)
        assert image_set_file.get_path() == kwargs["image_set_file"].get_path()
    if "sound_file" in kwargs:
        sound_file = fb.get_sound_file()
        assert isinstance(sound_file, SoundFileLoader)
        assert sound_file.get_path() == kwargs["sound_file"].get_path()


def test_build_from_nonexistent_dir(mocker) -> None:
    mock_file_bundle_list_constructor = mocker.patch(
        "ultratrace2.model.files.bundle.FileBundleList.__init__", return_value=None,
    )
    with pytest.raises(AssertionError):
        FileBundleList.build_from_dir("/tmp/this-does-not-exist-123123")
    mock_file_bundle_list_constructor.assert_not_called()


@pytest.mark.parametrize(
    "source_dir,expected_file_map,should_emit_warning",
    [
        (
            "./test-data/example-bundles/ex000",
            {"file00": [(TextGridLoader, "file00.TextGrid")]},
            False,
        ),
        (
            "./test-data/example-bundles/ex001",
            {
                "file00": [(TextGridLoader, "file00.TextGrid")],
                "file01": [(TextGridLoader, "file01.TextGrid")],
            },
            False,
        ),
        (
            "./test-data/example-bundles/ex002",
            {
                "file00": [
                    (MP3Loader, "file00.mp3"),
                    (TextGridLoader, "file00.TextGrid"),
                ]
            },
            False,
        ),
        (
            "./test-data/example-bundles/ex003",
            {
                "file00": [(TextGridLoader, "file00.TextGrid")],
                "file01": [(MP3Loader, "file01.mp3")],
            },
            False,
        ),
        (
            "./test-data/example-bundles/ex004",
            {
                "file00": [
                    (DICOMLoader, "file00.dicom"),
                    (MP3Loader, "file00.mp3"),
                    (TextGridLoader, "file00.TextGrid"),
                ]
            },
            False,
        ),
        ("./test-data/example-bundles/ex005", {}, False),
        ("./test-data/example-bundles/ex006", {}, True),
        (
            "./test-data/example-bundles/ex007",
            {"file00": [(TextGridLoader, "file00.TextGrid")]},
            True,
        ),
        (
            "./test-data/example-bundles/ex008",
            {
                "file00": [
                    (DICOMLoader, "file00.dicom"),
                    (MP3Loader, "file00.mp3"),
                    (TextGridLoader, "file00.TextGrid"),
                ],
                "file01": [
                    (DICOMLoader, "file01.dicom"),
                    (MP3Loader, "file01.mp3"),
                    (TextGridLoader, "file01.TextGrid"),
                ],
                "file02": [
                    (DICOMLoader, "file02.dicom"),
                    (MP3Loader, "file02.mp3"),
                    (TextGridLoader, "file02.TextGrid"),
                ],
            },
            False,
        ),
        (
            "./test-data/example-bundles/ex009",
            {"file00": [(WAVLoader, "file00.wav")]},
            True,
        ),
        (
            "./test-data/example-bundles/ex010",
            {"file00": [(TextGridLoader, "sub00/file00.TextGrid")]},
            False,
        ),
        (
            "./test-data/example-bundles/ex011",
            {
                "file00": [(TextGridLoader, "sub00/file00.TextGrid")],
                "file01": [(TextGridLoader, "sub01/sub00/sub00/sub00/file01.TextGrid")],
            },
            False,
        ),
        (
            "./test-data/example-bundles/ex012",
            {
                "file00": [
                    (MP3Loader, "sub01/sub00/sub00/sub00/file00.mp3"),
                    (TextGridLoader, "sub00/file00.TextGrid"),
                ]
            },
            False,
        ),
        (
            "./test-data/example-bundles/ex013",
            {"file00": [(TextGridLoader, "sub01/file00.TextGrid")]},
            True,
        ),
        (
            "./test-data/example-bundles/ex014",
            {"link00": [(TextGridLoader, "../ex004/file00.TextGrid")]},
            False,
        ),
        (
            "./test-data/example-bundles/ex015",
            {
                "file00": [(MP3Loader, "file00.mp3")],
                "link00": [(TextGridLoader, "../ex004/file00.TextGrid")],
            },
            False,
        ),
        (
            "./test-data/example-bundles/ex016",
            {
                "link00": [
                    (MP3Loader, "link00.mp3"),
                    (TextGridLoader, "../ex004/file00.TextGrid"),
                ]
            },
            False,
        ),
        (
            "./test-data/ftyers",
            {
                "20150629171639": [
                    (DICOMLoader, "20150629171639.dicom"),
                    (FLACLoader, "20150629171639.flac"),
                    (TextGridLoader, "20150629171639.TextGrid"),
                ],
            },
            True,
        ),
    ],
)
def test_build_from_dir(
    mocker,
    source_dir: str,
    expected_file_map: Dict[str, Sequence[Tuple[Type[FileLoaderBase], str]]],
    should_emit_warning: bool,
) -> None:
    mock_file_bundle_list_constructor = mocker.patch(
        "ultratrace2.model.files.bundle.FileBundleList.__init__", return_value=None,
    )
    mock_warning = mocker.patch("ultratrace2.model.files.bundle.logger.warning")
    FileBundleList.build_from_dir(source_dir)
    expected_bundles = {}
    for expected_name, expected_files in expected_file_map.items():
        alignment_file = None
        image_set_file = None
        sound_file = None
        for loader, source_subpath in expected_files:
            source_path = os.path.abspath(os.path.join(source_dir, source_subpath))
            if issubclass(loader, AlignmentFileLoader):
                alignment_file = loader.from_file(source_path)
            elif issubclass(loader, ImageSetFileLoader):
                image_set_file = loader.from_file(source_path)
            elif issubclass(loader, SoundFileLoader):
                sound_file = loader.from_file(source_path)
            else:
                raise RuntimeError("malformed input")
        expected_bundles[expected_name] = FileBundle(
            name=expected_name,
            alignment_file=alignment_file,
            image_set_file=image_set_file,
            sound_file=sound_file,
        )
    mock_file_bundle_list_constructor.assert_called_with(expected_bundles)
    if should_emit_warning:
        mock_warning.assert_called_once()
    else:
        mock_warning.assert_not_called()
