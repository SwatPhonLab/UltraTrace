import pytest

from ..project import Project


@pytest.mark.parametrize(
    "save_file,error",
    [
        ("", RuntimeError),
        ("/path/to/nowhere", RuntimeError),
        ("/dev/null", RuntimeError),  # pickle cannot open
        ("/etc/sudoers", RuntimeError),  # not readable
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
