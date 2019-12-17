from tkinter import filedialog as TkFileDialog

from . import Widget

class FileDialog(Widget):
    def __init__(self, app):
        super().__init__(app)

    def ask(self, *args, **kwargs):
        return TkFileDialog.askdirectory(*args, **kwargs)
