import os

from gui.widgets.filedialog import FileDialog

class IO:
    def __init__(self, app, args):

        self.app = app

    def get_directory(self, cwd=None):

        if cwd is None:
            cwd = os.getcwd()

        return FileDialog(self.app).ask(initialdir=cwd, title='Choose a directory')
