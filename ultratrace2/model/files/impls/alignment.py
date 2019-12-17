from typing import List

from ..ADT import TypedFile, TypedFileImpl


class Alignment(TypedFile):
    class TextGrid(TypedFileImpl):
        mimetypes = ["text/plain"]
        extensions = [".textgrid"]

        def load(self):
            raise NotImplementedError()

        @classmethod
        def recognizes(cls, mimetype: str, extension: str) -> bool:
            return mimetype in cls.mimetypes and extension in cls.extensions

    class Measurement(TypedFileImpl):
        # FIXME: what is this? do we need to support it?
        mimetypes = []
        extensions = []

        def load(self):
            raise NotImplementedError()

        @classmethod
        def recognizes(cls, mimetype: str, extension: str) -> bool:
            return mimetype in cls.mimetypes and extension in cls.extensions

    preferred_impls: List[TypedFileImpl] = [TextGrid, Measurement]

    def __init__(self):
        super().__init__()
