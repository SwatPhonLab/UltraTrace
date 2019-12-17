import tkinter as tk
from PIL import ImageTk

from .rect_tracker import RectTracker

class ZoomFrame(tk.Frame):
    WIDGET_WIDTH = 800
    WIDGET_HEIGHT = 600
    MIN_ZOOM = -5
    MAX_ZOOM = 5
    SCALE_FACTOR = 1.3
    def __init__(self, master, app):

        super().__init__(master)

        self.app = app

        self.canvas = tk.Canvas(
                master,
                bg='grey',
                width=self.WIDGET_WIDTH,
                height=self.WIDGET_HEIGHT,
                highlightthickness=0)
        self.canvas.update() # tkinter needs this or else it won't render the image

        self.canvas.bind('<Control-Button-1>', self.pan_start)
        self.canvas.bind('<Control-B1-Motion>', self.pan)
        self.canvas.bind('<MouseWheel>', self.zoom) # Windows / MacOS
        self.canvas.bind('<Button-4>', self.zoom_in) # Linux scroll up
        self.canvas.bind('<Button-5>', self.zoom_out) # Linux scroll down
        self.canvas.bind('<Button-1>', self.app.onClickZoom)
        self.canvas.bind('<Motion>', self.app.onMotion)

        self.app.bind('<Command-equal>', self.zoom_in)
        self.app.bind('<Command-minus>', self.zoom_out)

        RectTracker(self.canvas).autodraw(outline='blue')

        self.shown = False

        self.reset_canvas()

    def reset_canvas(self):

        self.image = None
        self.zoom = 0
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.pan_x = 0
        self.pan_y = 0

    def set_image(self, image):
        self.image = image
        self.show_image()

    def get_zoom_scale(self):
        return self.ZOOM_FACTOR ** self.zoom

    def show_image(self, event=None):
        self.canvas.delete('delendum')
        if self.image is None:
            return

        width, height = self.image.size
        scale = self.get_zoom_scale()

        self.container = self.canvas.create_rectangle(
                0,
                0,
                width,
                height,
                width=0,
                tags='delendum')
        self.canvas.scale('all', 0, 0, scale, scale)
        self.canvas.move('all', self.pan_x, self.pan_y)

        x0, y0, x1, y1 = self.canvas.bbox(self.container)
        scaled_image = self.image.resize((x1 - x0, y1 - y0))

        # save a reference so that python doesn't garbage collect it
        self.image_tk = ImageTk.PhotoImage(scaled_image)
        self.canvas.create_image(
                x0,
                y0,
                anchor='nw',
                image=self.image_tk,
                tags='delendum')
        self.canvas.lower('delendum')

    def zoom(self, event):
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def zoom_in(self):
        if self.image is not None and self.zoom > self.MIN_ZOOM:
            self.zoom += 1
            self.show_image()

    def zoom_out(self):
        if self.image is not None and self.zoom < self.MAX_ZOOM:
            self.zoom -= 1
            self.show_image()

    def pan_start(self, event):
        self.pan_start_x = event.x
        self.pan_start_y = event.y

    def pan(self, event):
        self.pan_x += event.x - self.pan_start_x
        self.pan_y += event.y - self.pan_start_y
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        self.show_image()

    def grid(self):
        self.canvas.grid(row=0, column=0, sticky='news')

    def grid_remove(self):
        self.canvas.grid_remove()

