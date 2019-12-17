from tkinter.filedialog import askdirectory as choose_dir
from typing import Optional

from .gui import GUI
from .model.project import Project


class App:
    def __init__(self, args): # FIXME: be more granular here

        if args.path is None:
            path = choose_dir()
            if not path:
                raise ValueError('You must choose a directory to open')
        else:
            path = args.path

        self.project = Project(path)
        self.gui = GUI(theme=args.theme)

    def main(self):
        pass


# singleton
app: Optional[App] = None


def initialize_app(args) -> App: # FIXME: be more granular here
    global app
    app = App(args)
    return app
