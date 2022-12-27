from .pydub import PydubLoader


class OggLoader(PydubLoader):
    @staticmethod
    def get_priority() -> int:
        return 2
