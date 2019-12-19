from argparse import Namespace
from tkinter.filedialog import askdirectory as choose_dir
from typing import Optional

from .gui import GUI
from .model.project import Project


class App:
    def __init__(self, args: Namespace):

        headless = getattr(args, "headless", False)

        path: Optional[str] = getattr(args, "path", None)
        if path is None and not headless:
            path = choose_dir()
        if not path:
            raise ValueError("You must choose a directory to open")

        self.project: Project = Project.get_by_path(path)

        if not headless:
            self.gui = GUI(theme=args.theme)

    def main(self) -> None:
        pass


# singleton
app: Optional[App] = None


def initialize_app(args: Namespace) -> App:
    global app
    app = App(args)
    return app
