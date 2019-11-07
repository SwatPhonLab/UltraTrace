import utils

from .colors import RED, get_random_color
from uuid import uuid4
from .xhairs import XHairsList

class TracesList:
    def __init__(self):

        default_trace = Trace('tongue', RED)
        self.traces = [default_trace]

    def __len__(self):
        return len(self.traces)

    def __iter__(self):
        for trace in self.traces:
            yield trace

    def __getitem__(self, index):
        if isinstance(index, int):
            return self.traces[index]
        elif isinstance(index, str):
            # FIXME this is inefficient :/
            for trace in self:
                if trace.id == index:
                    return trace
            raise KeyError(f'cannot find trace with index "{index}"')
        else:
            raise TypeError(f'cannot index traces with type "{type(index)}"')

    def add(self, trace):
        # FIXME configure MAX_NUM_TRACES
        self.traces.append(trace)

    def __repr__(self):
        return f'[{",".join(map(repr, self))}]'

    def __str__(self):
        return f'[{",".join(map(str, self))}]'

class Trace:
    def __init__(self, name, color=None):

        self.id = uuid4()
        self.name = name
        self.color = get_random_color() if color is None else color
        self.xhairs = XHairsList(self)

    def add(self, xhair):
        self.xhairs.add(xhair)

    def change_color(self):
        oldColor = self.color
        self.color = get_random_color()
        return oldColor

    def __repr__(self):
        return f'Trace<{self.id}>({self.name},{self.color})'

    def __str__(self):
        return f'Trace({self.name},{self.color})'
