from typing import IO, Sequence

import logging
import os
import tempfile
import textgrid  # type: ignore

from .base import AlignmentFileLoader, FileLoadError, Intervals


logger = logging.getLogger(__name__)


class TextGridInterval:
    def __init__(self, tg_interval: textgrid.Interval):
        self.tg_interval = tg_interval

    def get_start(self) -> float:
        return self.tg_interval.minTime

    def get_end(self) -> float:
        return self.tg_interval.maxTime

    def get_contents(self) -> str:
        return self.tg_interval.mark

    def __bool__(self) -> bool:
        return bool(self.get_contents())


class TextGridLoader(AlignmentFileLoader):
    def get_path(self) -> str:
        return self._path

    def set_path(self, path) -> None:
        self._path = path

    def __init__(self, path: str, tg_data: textgrid.TextGrid):
        self.set_path(path)
        self.tg_data = tg_data
        self.offset = 0.0

    def get_tier_names(self) -> Sequence[str]:
        return self.tg_data.getNames()

    def get_intervals(self) -> Intervals:
        all_intervals = []
        for tier in self.tg_data.tiers:
            if isinstance(tier, textgrid.PointTier):
                continue
            tier_intervals = []
            for tier_interval in tier:
                tg_interval = TextGridInterval(tier_interval)
                if not tg_interval:
                    continue
                tier_intervals.append(tg_interval)
            all_intervals.append((tier.name, tier_intervals))
        return all_intervals

    def get_start(self) -> float:
        return self.tg_data.minTime + self.offset

    def get_end(self) -> float:
        return self.tg_data.maxTime + self.offset

    def get_offset(self) -> float:
        return self.offset

    def set_offset(self, offset: float) -> None:
        self.offset = offset

    @classmethod
    def from_file(cls, path: str) -> "TextGridLoader":
        try:

            if not os.path.exists(path):
                raise FileNotFoundError(f"Cannot load from path: '{path}'")

            for encoding in (
                "utf-8",
                "utf-16",
                "Windows-1251",
                "Windows-1252",
                "ISO-8859-1",  # aka Latin-1
                "macroman",
            ):
                try:
                    tg_data = TextGridLoader.load_with_encoding(path, encoding)
                    return cls(path, tg_data)
                except UnicodeDecodeError:
                    pass
                except textgrid.exceptions.TextGridError as e:
                    logger.error(e)

            raise ValueError("Unable to parse file")

        except Exception as e:
            raise FileLoadError(
                f"Invalid TextGrid ({path}), unable to read: {str(e)}"
            ) from e

    @staticmethod
    def load_with_encoding(path: str, encoding: str) -> textgrid.TextGrid:
        if encoding == "utf-8" or encoding == "utf-16":
            return textgrid.TextGrid.fromFile(path)
        else:
            with tempfile.NamedTemporaryFile() as temp_file:
                TextGridLoader.copy_to_temp_file_with_encoding(
                    path, temp_file, encoding
                )
                return textgrid.TextGrid.fromFile(temp_file.name)

    @staticmethod
    def copy_to_temp_file_with_encoding(
        original_path: str, temp_file: IO[bytes], encoding: str
    ) -> None:
        with open(original_path, "rb") as orig_file:
            transcoded_contents = orig_file.read().decode(encoding).encode("utf-8")
            temp_file.write(transcoded_contents)
            temp_file.seek(0)
