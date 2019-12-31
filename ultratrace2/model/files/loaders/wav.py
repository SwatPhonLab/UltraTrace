from .pydub import PydubLoader


class WAVLoader(PydubLoader):
    @staticmethod
    def get_priority() -> int:
        return 3
