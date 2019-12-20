import logging
import os
import pickle

from .trace import TraceList
from .files.bundle import FileBundleList

logger = logging.getLogger(__name__)


class Project:
    def __init__(self, traces: TraceList, files: FileBundleList):
        """
        Internal function: to construct a Project, either call ::get_by_path()
        """
        self.traces = traces
        self.files = files

    def save(self):
        raise NotImplementedError()

    @classmethod
    def load(cls, save_file: str) -> "Project":
        with open(save_file, "rb") as fp:
            project = pickle.load(fp)
            assert isinstance(project, Project)
            return project

    @classmethod
    def get_by_path(cls, root_path: str) -> "Project":

        root_path = os.path.realpath(os.path.abspath(root_path))  # absolute path
        if not os.path.exists(root_path):
            raise ValueError(
                f"cannot initialize project at {root_path}: directory does not exist"
            )

        if not os.path.isdir(root_path):
            raise ValueError(
                f"cannot initialize project at {root_path}: not a directory"
            )

        save_dir = cls.get_save_dir(root_path)
        if not os.path.exists(save_dir):
            os.mkdir(save_dir, mode=0o755)

        save_file = cls.get_save_file(root_path)
        try:
            return cls.load(save_file)
        except Exception as e:
            logger.warning(e)
            logger.info(
                f"Unable to find existing project at {root_path}, creating new one..."
            )

        traces = TraceList()
        file_bundles = FileBundleList.build_from_dir(root_path)
        return cls(traces, file_bundles)

    @staticmethod
    def get_save_dir(path: str) -> str:
        return os.path.join(path, ".ultratrace")

    @staticmethod
    def get_save_file(path: str) -> str:
        save_dir = Project.get_save_dir(path)
        return os.path.join(save_dir, "project.pkl")

    def filepath(self):
        raise NotImplementedError()

    def current_trace(self):
        raise NotImplementedError()

    def current_frame(self):
        raise NotImplementedError()

    def has_alignment_impl(self) -> bool:
        return self.files.has_alignment_impl

    def has_image_impl(self) -> bool:
        return self.files.has_image_set_impl

    def has_sound_impl(self) -> bool:
        return self.files.has_sound_impl
