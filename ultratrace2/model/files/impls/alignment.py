from typing import ClassVar, Sequence

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

        mimetypes: ClassVar[Sequence[str]] = []
        extensions: ClassVar[Sequence[str]] = []

        def load(self):
            raise NotImplementedError()

        @classmethod
        def recognizes(cls, mimetype: str, extension: str) -> bool:
            return mimetype in cls.mimetypes and extension in cls.extensions

    preferred_impls = [TextGrid, Measurement]

    def __init__(self):
        super().__init__()
