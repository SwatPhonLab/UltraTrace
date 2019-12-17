import random

class Color:
    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b

    def __repr__(self):
        return f'Color(0x{self.r:02x},0x{self.g:02x},0x{self.b:02x})'

def get_random_color():
    return Color(
            random.randint(0x00, 0xff),
            random.randint(0x00, 0xff),
            random.randint(0x00, 0xff))

RED     = Color(0xff, 0x00, 0x00)
GREEN   = Color(0x00, 0xff, 0x00)
BLUE    = Color(0x00, 0x00, 0xff)

print(get_random_color())
