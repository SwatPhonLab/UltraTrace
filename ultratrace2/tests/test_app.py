from pathlib import Path
from typing import Any, Dict

import pytest

from .. import app as app_py
from ..app import App, initialize_app


@pytest.mark.parametrize(
    "kwargs,error",
    [
        (dict(headless=True), ValueError),
        (dict(headless=True, path="/path/to/nowhere"), ValueError),
        (dict(headless=True, path="/dev/null"), ValueError),  # not a directory
        (dict(headless=True, path="/"), PermissionError),  # not writeable
    ],
)
def test_initialize_app_invalid(
    kwargs: Dict[str, Any], error: Exception, tmpdir
) -> None:
    app_py.app = None  # overwrite global object
    with pytest.raises(error):
        initialize_app(**kwargs)


@pytest.mark.parametrize("kwargs", [(dict(headless=True)),])  # noqa: E231
def test_initialize_app_valid(kwargs: Dict[str, Any], tmp_path: Path) -> None:
    # overwrite global object
    app_py.app = None
    # initialize an empty dir
    path = tmp_path / "ultratrace-test-app"
    path.mkdir()
    # initialize
    kwargs["path"] = str(path)
    app = initialize_app(**kwargs)
    assert isinstance(app, App)
