from typing import Optional, IO

import logging
import os
import tempfile
import textgrid  # type: ignore

from .base import AlignmentFileLoader, FileLoadError


logger = logging.getLogger(__name__)


class TextGridLoader(AlignmentFileLoader):
    def get_path(self) -> str:
        return self._path

    def set_path(self, path) -> None:
        self._path = path

    def __init__(self, path: str, tg_data: textgrid.TextGrid):
        self.set_path(path)
        self.tg_data = tg_data

    @classmethod
    def from_file(cls, path: str) -> "TextGridLoader":
        try:

            if not os.path.exists(path):
                raise FileNotFoundError(f"Cannot load from path: '{path}'")

            for encoding in ("utf-8", "Windows-1251", "Windows-1252", "ISO-8859-1"):
                tg_data = TextGridLoader.try_load_with_encoding(path, encoding)
                return cls(path, tg_data)

            raise ValueError("Unable to parse file")

        except Exception as e:
            raise FileLoadError(
                f"Invalid TextGrid ({path}), unable to read: {str(e)}"
            ) from e

    @classmethod
    def try_load_with_encoding(
        cls, path: str, encoding: str
    ) -> Optional[textgrid.TextGrid]:
        try:
            if encoding == "utf-8":
                return textgrid.TextGrid.fromFile(path)
            else:
                transcoded_file = cls.copy_to_temp_file_with_encoding(path, encoding)
                return textgrid.TextGrid.fromFile(transcoded_file.name)
        except textgrid.exceptions.TextGridError as e:
            logger.error(e)
            raise  # FIXME: implement something here?

    @classmethod
    def copy_to_temp_file_with_encoding(
        cls, original_path: str, encoding: str
    ) -> IO[bytes]:
        # this gets ::close()d when it is GC'ed
        temp_file = tempfile.NamedTemporaryFile()
        with open(original_path, "rb") as orig_file:
            transcoded_contents = orig_file.read().decode(encoding).encode("utf-8")
            temp_file.write(transcoded_contents)
        return temp_file
