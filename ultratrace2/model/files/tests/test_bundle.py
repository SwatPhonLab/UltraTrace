import pytest

from ..bundle import FileBundle, FileBundleList


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
def test_empty_file_bundle_constructor(kwargs) -> None:
    fb = FileBundle("test", **kwargs)
    assert not fb.has_impl()
    assert str(fb) == 'Bundle("test",None,None,None,None)'


def test_build_from_nonexistent_dir(mocker) -> None:
    mock_file_bundle_list_constructor = mocker.patch(
        "ultratrace2.model.files.bundle.FileBundleList.__init__", return_value=None,
    )
    with pytest.raises(AssertionError):
        FileBundleList.build_from_dir("/tmp/this-does-not-exist-123123")
    mock_file_bundle_list_constructor.assert_not_called()


@pytest.mark.parametrize(
    "source_dir,bundle_map", [("./test-data/example-bundles/ex000", {})],
)
def test_build_from_dir(mocker, source_dir, bundle_map) -> None:
    mock_file_bundle_list_constructor = mocker.patch(
        "ultratrace2.model.files.bundle.FileBundleList.__init__", return_value=None,
    )
    FileBundleList.build_from_dir(source_dir)
    mock_file_bundle_list_constructor.assert_called_with(bundle_map)
