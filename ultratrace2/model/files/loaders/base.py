import logging

from abc import ABC, abstractmethod
from PIL import Image  # type: ignore
from typing import Type, TypeVar


logger = logging.getLogger(__name__)


class FileLoadError(Exception):
    pass


Self = TypeVar("Self", bound="FileLoaderBase")


class FileLoaderBase(ABC):
    def __new__(cls, path: str):
        try:
            return cls.from_file(path)
        except FileLoadError as e:
            logger.error(e)
            return None

    def __init__(self, path: str):
        self.path = path

    def __repr__(self):
        return f"{type(self).__name__}({self.path})"

    @classmethod
    @abstractmethod
    def from_file(cls: Type[Self], path: str) -> Self:
        # NB: If this concrete method fails to load the data at the given path, then
        #     it should throw a `FileLoadError`.
        pass


class AlignmentFileLoader(FileLoaderBase):
    pass


class ImageSetFileLoader(FileLoaderBase):
    @abstractmethod
    def __len__(self) -> int:
        """ImageSets should have some notion of their length.

        For example, for DICOM files, this is equal to the number of frames. This
        number can then be used to "slice up" any accompanying Alignment or Sound
        files.
        """

    @abstractmethod
    def get_frame(self, i: int) -> Image.Image:
        """ImageSets should support random access of frames."""
        pass


class SoundFileLoader(FileLoaderBase):
    pass
