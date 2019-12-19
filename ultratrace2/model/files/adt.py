import logging
import mimetypes
import os

from abc import ABC, abstractmethod
from typing import ClassVar, Sequence


logger = logging.getLogger(__name__)


class FileLoadError(Exception):
    pass


class TypedFile(ABC):

    extensions: ClassVar[Sequence[str]]
    mimetypes: ClassVar[Sequence[str]]

    _path: str

    @classmethod
    def is_valid(cls, path: str) -> bool:
        _, extension = os.path.splitext(path.lower())
        mimetype, _ = mimetypes.guess_type(path)
        return extension in cls.extensions and mimetype in cls.mimetypes

    @property
    @abstractmethod
    def path(self) -> str:
        return self._path

    def __new__(cls, path: str):
        try:
            return cls.from_file(path)
        except FileLoadError as e:
            logger.error(e)
            return None

    def __repr__(self):
        return f"{type(self).__name__}({self.path})"

    @classmethod
    @abstractmethod
    def from_file(cls, path: str) -> "TypedFile":
        pass


class AlignmentFile(TypedFile):
    pass


class ImageSetFile(TypedFile):
    pass


class SoundFile(TypedFile):
    pass
