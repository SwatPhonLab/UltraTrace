from .pydub import PydubLoader


class MP3Loader(PydubLoader):
    @staticmethod
    def get_priority() -> int:
        return 1
