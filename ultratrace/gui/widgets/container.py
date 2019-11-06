import utils

from . import Widget

class Container(Widget):
    def __init__(self, app, align, *children):
        super().__init__(app, align=align, children=children)
