from .base import SoundFileLoader


class OggLoader(SoundFileLoader):
    @classmethod
    def from_file(cls, path: str) -> "OggLoader":
        raise NotImplementedError()
