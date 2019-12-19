from tkinter.filedialog import askdirectory as choose_dir
from typing import Optional

from .gui import GUI
from .model.project import Project


class App:
    def __init__(
        self,
        headless: bool = False,
        path: Optional[str] = None,
        theme: Optional[str] = None,
    ):

        if path is None and not headless:
            path = choose_dir()
        if not path:
            raise ValueError("You must choose a directory to open")

        self.project: Project = Project.get_by_path(path)

        if not headless:
            self.gui = GUI(theme=theme)

    def main(self) -> None:
        pass


# singleton
app: Optional[App] = None


def initialize_app(
    headless: bool = False, path: Optional[str] = None, theme: Optional[str] = None
) -> App:

    global app
    app = App(headless=headless, path=path, theme=theme,)
    return app
