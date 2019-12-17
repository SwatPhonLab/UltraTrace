import os

from .trace import TraceList
from .files.bundle import FileBundleList


class Project:
    def __init__(self, path: str):
        if not os.path.exists(path):
            raise ValueError(f"cannot initialize project at {path}")
        self.root_path = os.path.realpath(os.path.abspath(path))  # absolute path
        self.traces = TraceList()
        self.files = FileBundleList(self.root_path)

    def save(self):
        raise NotImplementedError()

    @classmethod
    def load(cls):
        raise NotImplementedError()

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
