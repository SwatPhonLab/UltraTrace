import logging

from abc import ABC, abstractmethod
from PIL import Image  # type: ignore
from typing import Sequence, Tuple, Type, TypeVar
from typing_extensions import Protocol


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

    def __repr__(self):
        return f"{type(self).__name__}({self.get_path()})"

    @classmethod
    @abstractmethod
    def from_file(cls: Type[Self], path: str) -> Self:
        """Construct an instance from a path.

        NB: If this concrete method fails to load the data at the given path, then
            it should throw a `FileLoadError`."""

    def __eq__(self, other):
        return self.get_path() == other.get_path() and type(self) == type(other)

    @staticmethod
    def get_priority() -> int:
        return 0


class IntervalBase(Protocol):
    def get_start(self) -> float:
        ...

    def get_end(self) -> float:
        ...

    def get_contents(self) -> str:
        ...

    def __bool__(self) -> bool:
        ...


# NB: the Tuple is <interval_name, intervals>
Intervals = Sequence[Tuple[str, Sequence[IntervalBase]]]


class AlignmentFileLoader(FileLoaderBase):
    @abstractmethod
    def get_tier_names(self) -> Sequence[str]:
        ...

    @abstractmethod
    def get_intervals(self) -> Intervals:
        ...

    @abstractmethod
    def get_start(self) -> float:
        ...

    @abstractmethod
    def get_end(self) -> float:
        ...

    @abstractmethod
    def get_offset(self) -> float:
        ...

    @abstractmethod
    def set_offset(self, offset: float) -> None:
        ...


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

    @abstractmethod
    def get_height(self) -> int:
        ...

    @abstractmethod
    def get_width(self) -> int:
        ...


class SoundFileLoader(FileLoaderBase):
    @abstractmethod
    def __len__(self) -> int:
        """Length of file in ms"""
