from tkinter.filedialog import askdirectory as choose_dir
from typing import Optional

from .model.project import Project


class App:
    def __init__(
        self, path: str, headless: bool = False, theme: Optional[str] = None,
    ):

        self.project: Project = Project.get_by_path(path)

    def main(self) -> None:
        pass


# singleton
app: Optional[App] = None


def initialize_app(
    path: str, headless: bool = False, theme: Optional[str] = None
) -> App:

    global app
    app = App(path, headless=headless, theme=theme,)
    return app
