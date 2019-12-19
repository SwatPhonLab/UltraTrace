import math

import pytest

from ..xhair import XHair
from ..color import Color


def _get_black() -> Color:
    return Color(0, 0, 0)


@pytest.mark.parametrize(
    "p,q,expected",
    [
        (XHair(_get_black, 0, 0), XHair(_get_black, 1, 0), 1),
        (XHair(_get_black, 0, 0), XHair(_get_black, 1, 1), 2),
        (XHair(_get_black, 2, 0), XHair(_get_black, 0, 2), 8),
        (XHair(_get_black, math.inf, 0), XHair(_get_black, 0, 0), math.inf),
    ],
)
def test_sq_dist_from(p: XHair, q: XHair, expected: float):
    assert p.sq_dist_from(q) == q.sq_dist_from(p) == expected


def test_get_color():
    x = XHair(_get_black, 0, 0)
    assert x.get_color() == Color(0, 0, 0)


def test_get_color_with_mutation():
    class ColorRef:
        def __init__(self, initial_color: Color):
            self._color = initial_color

        def get_color(self) -> Color:
            return self._color

        def set_color(self, color: Color) -> None:
            self._color = color

    initial_color = Color(0, 0, 0)
    final_color = Color(0, 100, 0)
    ref = ColorRef(initial_color)

    x = XHair(ref.get_color, 0, 0)
    color_pre_set = x.get_color()
    ref.set_color(final_color)
    color_post_set = x.get_color()

    assert color_pre_set == initial_color
    assert color_post_set != color_pre_set
    assert color_post_set == final_color
