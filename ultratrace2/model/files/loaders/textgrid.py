from .base import AlignmentFileLoader


class TextGridLoader(AlignmentFileLoader):
    @classmethod
    def from_file(cls, path: str) -> "TextGridLoader":
        raise NotImplementedError()
