from .base import Module
import tkinter as tk

class Metadata(Module):
    def __init__(self, app, path):
        path = tk.filedialog.askdirectory(initialdir=os.getcwd(), title="Choose a directory")
