import logging
import numpy as np

from abc import ABC, abstractmethod
from PIL import Image  # type: ignore
from typing import Optional, Sequence, Tuple, Type, TypeVar
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


Spectrogram = np.ndarray


class SoundFileLoader(FileLoaderBase):
    @abstractmethod
    def __len__(self) -> int:
        """Length of file in ms"""

    @abstractmethod
    def get_spectrogram(
        self,
        start_time_ms: int,
        stop_time_ms: int,
        window_length: float,
        max_frequency: float,
        dynamic_range: float,
        n_slices: int,
    ) -> Optional[Spectrogram]:
        """Return a numpy array representing the pixels in a spectrogram.

        Ultimately, we should probably cache this to disk somehow, either
        by converting it directly into a PNG via PIL or saving the raw array,
        since the FFT operations are comparatively slow.

        For now, at least until we have a stable API, it makes sense to me
        to just generate this on-the-fly."""
