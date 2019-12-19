from contextlib import nullcontext
from typing import Any, Optional, Type, Union

import pytest

from ..color import Color


@pytest.mark.parametrize(
    "r,g,b,error",
    [
        (0, 0, 0, None),
        (255, 255, 255, None),
        (-1, 0, 0, ValueError),
        (0, -1, 0, ValueError),
        (0, 0, -1, ValueError),
        (256, 0, 0, ValueError),
        (0, 256, 0, ValueError),
        (0, 0, 256, ValueError),
    ],
)
def test_color(r: int, g: int, b: int, error: Optional[Type[Exception]]):
    ctx = pytest.raises(error) if error is not None else nullcontext()
    with ctx:
        Color(r, g, b)


@pytest.mark.parametrize(
    "raw_value,expected", [(0, 0), (255, 255), (-1, ValueError), (256, ValueError)]
)
def test_set_r(raw_value: int, expected: Union[int, Type[Exception]]):
    c = Color(100, 100, 100)
    if isinstance(expected, int):
        c.r = raw_value
        assert c.r == expected
    elif issubclass(expected, Exception):
        with pytest.raises(expected):
            c.r = raw_value
    else:
        raise AssertionError()


@pytest.mark.parametrize(
    "color,other,should_be_equal",
    [
        (Color(0, 0, 0), Color(0, 0, 0), True),
        (Color(0, 0, 1), Color(0, 0, 0), False),
        (Color(0, 0, 0), "not a color", False),
    ],
)
def test_color_eq(color: Color, other: Any, should_be_equal: bool):
    if should_be_equal:
        assert color == other
    else:
        assert color != other
