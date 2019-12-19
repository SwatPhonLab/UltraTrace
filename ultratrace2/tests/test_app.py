from argparse import Namespace
from pathlib import Path

import pytest

from .. import app as app_py
from ..app import App, initialize_app


@pytest.mark.parametrize(
    "args,expected",
    [
        (Namespace(headless=True), ValueError),
        (Namespace(headless=True, path="/path/to/nowhere"), ValueError),
        (Namespace(headless=True, path="/dev/null"), ValueError),  # not a directory
        (Namespace(headless=True, path="/"), PermissionError),  # not writeable
    ],
)
def test_initialize_app_invalid(args: Namespace, expected: Exception, tmpdir) -> None:
    app_py.app = None  # overwrite global object
    with pytest.raises(expected):
        initialize_app(args)


@pytest.mark.parametrize("args", [(Namespace(headless=True)),])  # noqa: E231
def test_initialize_app_valid(args: Namespace, tmp_path: Path) -> None:
    # overwrite global object
    app_py.app = None
    # initialize an empty dir
    path = tmp_path / "ultratrace-test-app"
    path.mkdir()
    # save that to the Namespace
    args.path = path
    # initialize
    app = initialize_app(args)
    assert isinstance(app, App)
