import tkinter as tk


class Div(tk.Frame):
    def __init__(self, parent, children=[], sticky=""):
        super().__init__(parent)

    def grid(self, *args, **kwargs):
        super().grid(*args, **kwargs)

    def grid_remove(self):
        super().grid_remove()
