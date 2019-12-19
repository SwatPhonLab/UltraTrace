from .base import SoundFileLoader


class FLACLoader(SoundFileLoader):
    @classmethod
    def from_file(cls, path: str) -> "FLACLoader":
        raise NotImplementedError()
