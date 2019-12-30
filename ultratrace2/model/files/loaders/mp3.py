import pydub  # type: ignore

from .base import FileLoadError, SoundFileLoader


class MP3Loader(SoundFileLoader):
    def get_path(self) -> str:
        return self._path

    def set_path(self, path) -> None:
        self._path = path

    def __init__(self, path: str, audio_segment: pydub.AudioSegment):
        self.set_path(path)
        self.audio_segment = audio_segment

    def __len__(self) -> int:
        return len(self.audio_segment)

    @classmethod
    def from_file(cls, path: str) -> "MP3Loader":
        try:
            audio_segment = pydub.AudioSegment.from_file(path)
            return MP3Loader(path, audio_segment)
        except Exception as e:
            raise FileLoadError(
                f"Invalid MP3 ({path}), unable to read: {str(e)}"
            ) from e
