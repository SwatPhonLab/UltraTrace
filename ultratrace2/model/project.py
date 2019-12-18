import os
import pickle

from .trace import TraceList
from .files.bundle import FileBundleList


class Project:
    def __init__(self, path: str):
        """
        Internal function: to construct a Project, either call via ::initialize_from_path()
        or ::load().
        """
        if not os.path.exists(path):
            raise ValueError(f"cannot initialize project at {path}")
        self.root_path = os.path.realpath(os.path.abspath(path))  # absolute path
        self.traces = TraceList()
        self.files = FileBundleList()

    def save(self):
        raise NotImplementedError()

    @classmethod
    def load(cls, project_path) -> "Project":
        with open(project_path, "rb") as fp:
            project = pickle.load(fp)
            assert isinstance(project, Project)
            return project

    @classmethod
    def initialize_from_path(cls, data_path) -> "Project":
        project = Project(data_path)
        project.scan_files()
        return project

    def scan_files(self) -> None:
        self.files.scan_dir(self.root_path)

    def filepath(self):
        raise NotImplementedError()

    def current_trace(self):
        raise NotImplementedError()

    def current_frame(self):
        raise NotImplementedError()

    def has_alignment_impl(self) -> bool:
        return self.files.has_alignment_impl

    def has_image_impl(self) -> bool:
        return self.files.has_image_impl

    def has_sound_impl(self) -> bool:
        return self.files.has_sound_impl
