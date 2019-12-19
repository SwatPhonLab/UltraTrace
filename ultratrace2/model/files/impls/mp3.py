from typing import ClassVar, Sequence

from ..adt import TypedFile


class MP3(TypedFile):
    mimetypes: ClassVar[Sequence[str]] = []
    extensions: ClassVar[Sequence[str]] = []
