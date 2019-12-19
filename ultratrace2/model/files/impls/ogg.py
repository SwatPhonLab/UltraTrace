from typing import ClassVar, Sequence

from ..adt import TypedFile


class Ogg(TypedFile):
    mimetypes: ClassVar[Sequence[str]] = []
    extensions: ClassVar[Sequence[str]] = []
