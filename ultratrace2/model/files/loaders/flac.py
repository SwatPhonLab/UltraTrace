from .pydub import PydubLoader


class FLACLoader(PydubLoader):
    @staticmethod
    def get_priority() -> int:
        return 4
