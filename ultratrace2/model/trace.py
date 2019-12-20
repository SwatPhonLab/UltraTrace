from collections import OrderedDict
from typing import ClassVar, Dict, Optional, Set, TYPE_CHECKING
from uuid import uuid4, UUID

from .color import Color, get_random_color, RED
from .xhair import XHair

if TYPE_CHECKING:
    from .files.bundle import FileBundle


class Trace:

    DEFAULT_TRACE_NAME: ClassVar[str] = "tongue"
    DEFAULT_TRACE_COLOR: ClassVar[Color] = RED

    def __init__(self, name: str, color: Color):
        self.id: UUID = uuid4()
        self.is_visible: bool = True
        self.xhairs: Dict["FileBundle", Dict[int, Set[XHair]]] = {}
        self.name = name
        self.color = color

    def get_color(self) -> Color:
        return self.color

    def change_color(self, new_color: Optional[Color]) -> Color:
        if new_color is None:
            new_color = get_random_color()
        old_color = self.color
        self.color = new_color
        return old_color

    def get_name(self) -> str:
        return self.name

    def change_name(self, new_name: str) -> str:
        old_name = self.name
        self.name = new_name
        return old_name

    def show(self) -> None:
        self.is_visible = True

    def hide(self) -> None:
        self.is_visible = False

    def add_xhair(self, bundle: "FileBundle", frame: int, x: float, y: float) -> None:
        if bundle not in self.xhairs:
            self.xhairs[bundle] = {}
        if frame not in self.xhairs[bundle]:
            self.xhairs[bundle][frame] = set()
        xhair = XHair(self.get_color, x, y)
        self.xhairs[bundle][frame].add(xhair)


class TraceList:
    def __init__(self):
        self.traces: OrderedDict[UUID, Trace] = OrderedDict()
        default_trace = self.add_trace(
            Trace.DEFAULT_TRACE_NAME, Trace.DEFAULT_TRACE_COLOR,
        )
        self.default_trace: Trace = default_trace
        self.selected_trace: Trace = default_trace

    def add_trace(self, name: str, color: Color) -> Trace:
        trace = Trace(name, color)
        self.traces[trace.id] = trace
        return trace

    def get_default_trace(self) -> Trace:
        return self.default_trace

    def set_default_trace(self, trace: Trace) -> None:
        self.default_trace = trace

    def get_selected_trace(self) -> Trace:
        return self.selected_trace

    def set_selected_trace(self, trace: Trace) -> None:
        self.selected_trace = trace
