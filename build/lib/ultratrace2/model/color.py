import random
from typing import Any

PIXEL_MIN = 0
PIXEL_MAX = 255


def _pixel_value(raw_value: int) -> int:
    if not (PIXEL_MIN <= raw_value <= PIXEL_MAX):
        raise ValueError(
            f"Color must be in [{PIXEL_MIN}, {PIXEL_MAX}], but got {raw_value}"
        )
    return raw_value


class Color:
    def __init__(self, r: int, g: int, b: int):
        self._r = _pixel_value(r)
        self._g = _pixel_value(g)
        self._b = _pixel_value(b)

    @property
    def r(self) -> int:
        return self._r

    @r.setter
    def r(self, raw_value: int) -> None:
        self._r = _pixel_value(raw_value)

    @property
    def g(self) -> int:
        return self._g

    @g.setter
    def g(self, raw_value: int) -> None:
        self._g = _pixel_value(raw_value)

    @property
    def b(self) -> int:
        return self._b

    @b.setter
    def b(self, raw_value: int) -> None:
        self._b = _pixel_value(raw_value)

    def __repr__(self) -> str:
        return f"Color(0x{self.r:02x},0x{self.g:02x},0x{self.b:02x})"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return False
        return self.r == other.r and self.g == other.g and self.b == other.b


def get_random_color() -> Color:
    return Color(
        random.randint(PIXEL_MIN, PIXEL_MAX),
        random.randint(PIXEL_MIN, PIXEL_MAX),
        random.randint(PIXEL_MIN, PIXEL_MAX),
    )


RED = Color(PIXEL_MAX, PIXEL_MIN, PIXEL_MIN)
GREEN = Color(PIXEL_MIN, PIXEL_MAX, PIXEL_MIN)
BLUE = Color(PIXEL_MIN, PIXEL_MIN, PIXEL_MAX)
