from typing import Optional

from uuid import uuid4
from .color import Color, get_random_color, RED


class Trace:
    def __init__(self, name: str, color: Optional[Color] = None):
        self.id = uuid4()
        self.is_visible = True
        self.name = name
        self.color = color

    def change_color(self, new_color: Optional[Color] = None) -> Color:
        if new_color is None:
            new_color = get_random_color()
        old_color = self.color
        self.color = new_color
        return old_color

    def change_name(self, new_name: str) -> str:
        old_name = self.name
        self.name = new_name
        return old_name


class TraceList:
    pass
