from uuid import uuid4


class XHair:
    SELECTED_COLOR = "blue"
    SELECTED_WIDTH = 1.5
    UNSELECTED_WIDTH = 1
    RADIUS = 10

    def __init__(self, canvas, trace, x, y, **kwargs):

        self.id = uuid4()
        self.canvas = canvas
        self.trace = trace
        self.x = x
        self.y = y

        self.is_selected = False
        self.is_hidden = False

        self.h_line = self.canvas.create_line(
            x - 10,
            y,
            x + 10,
            y,
            tag=self.id,
            width=self.get_width(),
            fill=self.get_color(),
        )
        self.v_line = self.canvas.create_line(
            x,
            y - 10,
            x,
            y + 10,
            tag=self.id,
            width=self.get_width(),
            fill=self.get_color(),
        )

    def sq_dist_from(self, other):
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

    def get_width(self):
        return self.SELECTED_WIDTH if self.is_selected else self.UNSELECTED_WIDTH

    def get_color(self):
        return self.SELECTED_COLOR if self.is_selected else self.trace.get_color()

    def get_state(self):
        return "hidden" if self.is_hidden else "normal"

    def toggle_select(self):
        self.is_selected = not self.is_selected
        self.redraw()

    def select(self):
        self.is_selected = True
        self.redraw()

    def unselect(self):
        self.is_selected = False
        self.redraw()

    def show(self):
        self.is_hidden = False
        self.redraw()

    def hide(self):
        self.is_hidden = True
        self.redraw()

    def move(self, x, y):
        dx = x - self.x
        dy = y - self.y
        self.canvas.move(self.id, dx, dy)
        self.x = x
        self.y = y

    def redraw(self):
        self.canvas.itemconfig(
            self.id,
            width=self.get_width(),
            fill=self.get_color(),
            state=self.get_state(),
        )
