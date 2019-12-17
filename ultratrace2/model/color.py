import random


class Color:
    def __init__(self, r: int, g: int, b: int):
        self.r = r
        self.g = g
        self.b = b

    def __repr__(self) -> str:
        return f"Color(0x{self.r:02x},0x{self.g:02x},0x{self.b:02x})"


def get_random_color() -> Color:
    return Color(
        random.randint(0x00, 0xFF),
        random.randint(0x00, 0xFF),
        random.randint(0x00, 0xFF),
    )


RED = Color(0xFF, 0x00, 0x00)
GREEN = Color(0x00, 0xFF, 0x00)
BLUE = Color(0x00, 0x00, 0xFF)
