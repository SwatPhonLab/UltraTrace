import os
import pickle

from tkinter.filedialog import askdirectory as choose_dir
from typing import Optional, Set

from .gui import GUI
from .model.project import Project


class App:
    def __init__(self, args):  # FIXME: be more granular here

        if args.path is None:
            path = choose_dir()
            if not path:
                raise ValueError("You must choose a directory to open")
        else:
            path = args.path

        # FIXME: allow changing the $HOME-as-root via command line arg?
        self.ultratrace_home = os.path.join(os.environ["HOME"], ".ultratrace")
        if not os.path.exists(self.ultratrace_home):
            os.mkdir(self.ultratrace_home)

        self.project_hashes: Set[int]
        if os.path.exists(self.get_projects_path()):
            with open(self.get_projects_path(), "rb") as fp:
                project_hashes = pickle.load(fp)
                assert isinstance(project_hashes, set)
                for project_hash in project_hashes:
                    assert isinstance(project_hash, int)
                self.project_hashes = project_hashes
        else:
            self.project_hashes = set()

        self.project: Project = self.get_project_by_path(path)
        self.gui = GUI(theme=args.theme)

    def get_projects_path(self) -> str:
        return os.path.join(self.ultratrace_home, "projects.pkl")

    def get_project_path(self, project_hash: int) -> str:
        return os.path.join(self.ultratrace_home, "projects", str(project_hash))

    def get_project_by_path(self, path: str) -> Project:
        project_hash = hash(path)
        if project_hash in self.project_hashes:
            project_path = self.get_project_path(project_hash)
            return Project.load(project_path)
        return Project.initialize_from_path(path)

    def main(self) -> None:
        pass


# singleton
app: Optional[App] = None


def initialize_app(args) -> App:  # FIXME: be more granular here
    global app
    app = App(args)
    return app
