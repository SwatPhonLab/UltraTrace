from tkinter import filedialog as TkFileDialog

from . import Widget


class FileDialog(Widget):
    def __init__(self):
        super().__init__()

    def ask(self, *args, **kwargs):
        return TkFileDialog.askdirectory(*args, **kwargs)
