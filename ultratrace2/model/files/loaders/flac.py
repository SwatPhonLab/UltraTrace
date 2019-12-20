from .base import SoundFileLoader


class FLACLoader(SoundFileLoader):
    def get_path(self) -> str:
        return self._path

    def set_path(self, path) -> None:
        self._path = path

    def __init__(self, path: str):
        self.set_path(path)

    @classmethod
    def from_file(cls, path: str) -> "FLACLoader":
        raise NotImplementedError()
