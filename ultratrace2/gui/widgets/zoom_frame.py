import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageTk  # type: ignore

from .xhair import XHair


class Trace:
    def get_color(self):
        return "black"


class ZoomFrame(tk.Frame):
    """
    Valid **kwargs for tk.Frame:
     - background (bg)
     - borderwidth (bd)
     - colormap
     - container
     - cursor
     - height
     - highlightbackground
     - highlightcolor
     - highlightthickness
     - relief
     - takefocus
     - visual
     - width
    """

    DEFAULT_WIDTH = 800
    DEFAULT_HEIGHT = 600
    MIN_ZOOM = -5
    MAX_ZOOM = 5

    def __init__(self, master, **kwargs):

        super().__init__(master, **kwargs)
        self.canvas = tk.Canvas(
            self,
            bg="grey",
            width=self.DEFAULT_WIDTH,
            height=self.DEFAULT_HEIGHT,
            highlightthickness=0,
        )
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_mousemove)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        self.image_container = None
        self.image = None
        self.zoom = 0

        ###
        self.delta = 1.3
        self.canvas_width = 800
        self.width = 0
        self.canvas_height = 600
        self.height = 0
        self.shown = False
        self.aspect_ratio = 4 / 3
        self.orig_x = self.canvas.xview()[0] - 1
        self.orig_y = self.canvas.yview()[0] - 150
        self.image_scale = 1.0
        self.pan_start_x = 0
        self.pan_x = 0
        self.pan_start_y = 0
        self.pan_y = 0

        self.zoom_in_button = ttk.Button(master, text="zoom in", command=self.zoom_in)
        self.zoom_in_button.grid(column=1, row=0)

        self.zoom_out_button = ttk.Button(
            master, text="zoom out", command=self.zoom_out
        )
        self.zoom_out_button.grid(column=1, row=1)
        ###

        self.set_image(
            Image.open(
                "/Users/user/Pictures/Photo Booth Library/Pictures/Photo on 6-28-19 at 10.10 AM.jpg"
            )
        )
        self.is_dragging = False

        self.xhairs = {}  # Dict<XHair::id, XHair>

    def set_image(self, image):

        self.image_container = self.canvas.create_rectangle(
            0, 0, 0, 0, tags="container"
        )
        container_x0, container_y0, container_x1, container_y1 = self.canvas.bbox(
            self.image_container
        )

        self.image = image.resize(
            (container_x1 - container_x0, container_y1 - container_y0)
        )

        # We need to keep a reference around to prevent Python from garbage-collecting
        # it from underneath us.
        self.image_tk = ImageTk.PhotoImage(image)

        self.canvas.create_image(0, 0, image=self.image_tk, tags="image")
        self.canvas.lower("image")

    def on_click(self, event):
        # FIXME: handle Shift+Click
        print(event)
        click_position = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
        closest_xhair = None
        closest_xhair_sq_dist = float("inf")
        for xhair in self.xhairs.values():
            sq_dist = xhair.sq_dist_from(click_position)
            print(xhair, sq_dist)
            if sq_dist < (XHair.RADIUS ** 2) and sq_dist < closest_xhair_sq_dist:
                closest_xhair = xhair
                closest_xhair_sq_dist = sq_dist

        if closest_xhair is None:
            xhair = XHair(self.canvas, Trace(), event.x, event.y)
            self.xhairs[xhair.id] = xhair
        else:
            closest_xhair.toggle_select()

    def on_mousemove(self, event):
        print(event)

    def on_release(self, event):
        print(event)

    def zoom_in(self):
        pass

    def zoom_out(self):
        pass

    def grid(self, **kwargs):
        super(ZoomFrame, self).grid(**kwargs)
        self.canvas.grid(sticky="news", column=0, row=0, rowspan=2)

    def grid_remove(self):
        super().grid_remove()
        self.canvas.grid_remove()
