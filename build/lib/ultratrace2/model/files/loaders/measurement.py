from typing import Sequence

from .base import AlignmentFileLoader, Intervals


class MeasurementLoader(AlignmentFileLoader):
    # FIXME: what is this? do we need to support it?

    def get_path(self) -> str:
        return self._path

    def set_path(self, path) -> None:
        self._path = path

    def __init__(self, path: str):
        self.set_path(path)

    def get_tier_names(self) -> Sequence[str]:
        raise NotImplementedError()

    def get_intervals(self) -> Intervals:
        raise NotImplementedError()

    def get_start(self) -> float:
        raise NotImplementedError()

    def get_end(self) -> float:
        raise NotImplementedError()

    def get_offset(self) -> float:
        raise NotImplementedError()

    def set_offset(self, offset: float) -> None:
        raise NotImplementedError()

    @classmethod
    def from_file(cls, path: str) -> "MeasurementLoader":
        raise NotImplementedError()
