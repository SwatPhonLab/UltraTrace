import pytest

from ..project import Project
from ..trace import TraceList
from ..files.bundle import FileBundle, FileBundleList


@pytest.mark.parametrize(
    "save_file,error",
    [
        ("", FileNotFoundError),
        ("/path/to/nowhere", FileNotFoundError),
        ("/dev/null", EOFError),  # pickle cannot open
        ("/etc/sudoers", PermissionError),  # not readable
    ],
)
def test_load_project_invalid(save_file: str, error: Exception) -> None:
    with pytest.raises(error):
        Project.load(save_file)


# FIXME: not implemented, so can't test :/
"""
def test_load_project_valid(save_file) -> None:
    pass
"""


@pytest.mark.parametrize(
    "traces,files",
    [
        (TraceList(), FileBundleList({})),
        (TraceList(), FileBundleList({"x": FileBundle("x")})),
    ],
)
def test_init_project(traces: TraceList, files: FileBundleList) -> None:
    p = Project(traces, files)
    assert isinstance(p, Project)
