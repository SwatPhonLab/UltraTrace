import logging

from abc import ABC, abstractmethod
from PIL import Image  # type: ignore
from typing import Type, TypeVar


logger = logging.getLogger(__name__)


class FileLoadError(Exception):
    pass


Self = TypeVar("Self", bound="FileLoaderBase")


class FileLoaderBase(ABC):
    @abstractmethod
    def get_path(self) -> str:
        ...

    @abstractmethod
    def set_path(self, path) -> None:
        ...

    path = property(get_path, set_path)

    def __repr__(self):
        return f"{type(self).__name__}({self.path})"

    @classmethod
    @abstractmethod
    def from_file(cls: Type[Self], path: str) -> Self:
        """Construct an instance from a path.

        NB: If this concrete method fails to load the data at the given path, then
            it should throw a `FileLoadError`."""


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
