from .base import SoundFileLoader


class MP3Loader(SoundFileLoader):
    @classmethod
    def from_file(cls, path: str) -> "MP3Loader":
        raise NotImplementedError()
