from .base import SoundFileLoader


class WAVLoader(SoundFileLoader):
    @classmethod
    def from_file(cls, path: str) -> "WAVLoader":
        raise NotImplementedError()
