from typing import Tuple, TYPE_CHECKING, Union
from uuid import uuid4

if TYPE_CHECKING:
    from .color import Color
    from .trace import Trace


class XHair:
    def __init__(self, trace: Trace, x: float, y: float):

        self.id = uuid4()
        self.trace = trace
        self.x = x
        self.y = y

        self.is_selected = False
        self.is_hidden = False

    def sq_dist_from(self, other: Union["XHair", Tuple[float, float]]) -> float:
        # Euclidean distance squared, since sqrt() is relatively slow :^)
        if isinstance(other, XHair):
            dx = self.x - other.x
            dy = self.y - other.y
        elif isinstance(other, tuple):
            dx = self.x - other[0]
            dy = self.y - other[1]
        return (dx ** 2) + (dy ** 2)

    def __repr__(self):
        return f"XHair(id={self.id}, x={self.x}, y={self.y})"

    def toggle_select(self) -> None:
        self.is_selected = not self.is_selected

    def select(self) -> None:
        self.is_selected = True

    def unselect(self) -> None:
        self.is_selected = False

    def show(self):
        self.is_hidden = False

    def hide(self):
        self.is_hidden = True

    def move(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    def get_color(self) -> Color:
        return self.trace.get_color()
