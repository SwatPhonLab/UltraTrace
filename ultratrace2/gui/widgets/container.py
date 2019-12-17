from . import Widget


class Container(Widget):
    def __init__(self, align, *children):
        super().__init__(align=align, children=children)
