import random


class Color:
    def __init__(self, r: int, g: int, b: int):
        self.r = r
        self.g = g
        self.b = b

    def __repr__(self) -> str:
        return f'Color(0x{self.r:02x},0x{self.g:02x},0x{self.b:02x})'


def get_random_color() -> Color:
    return Color(
        random.randint(0x00, 0xff),
        random.randint(0x00, 0xff),
        random.randint(0x00, 0xff),
    )


RED = Color(0xff, 0x00, 0x00)
GREEN = Color(0x00, 0xff, 0x00)
BLUE = Color(0x00, 0x00, 0xff)

print(get_random_color())
