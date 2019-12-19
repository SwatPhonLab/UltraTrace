from typing import ClassVar, Sequence

from ..adt import AlignmentFile


class Measurement(AlignmentFile):
    # FIXME: what is this? do we need to support it?

    mimetypes: ClassVar[Sequence[str]] = []
    extensions: ClassVar[Sequence[str]] = []
