from typing import Optional

import logging
import numpy as np
import pydub  # type: ignore
import warnings

from .base import FileLoadError, SoundFileLoader, Spectrogram


logger = logging.getLogger(__name__)


class PydubLoader(SoundFileLoader):
    def get_path(self) -> str:
        return self._path

    def set_path(self, path) -> None:
        self._path = path

    def __init__(self, path: str, audio_segment: pydub.AudioSegment):
        self.set_path(path)
        self.audio_segment = audio_segment

    def __len__(self) -> int:
        return len(self.audio_segment)

    @classmethod
    def from_file(cls, path: str) -> "PydubLoader":
        try:
            audio_segment = pydub.AudioSegment.from_file(path)
            return PydubLoader(path, audio_segment)
        except Exception as e:
            raise FileLoadError(f"Invalid AudioSegment ({path}), unable to read") from e

    def get_spectrogram(
        self,
        start_time_ms: int,
        stop_time_ms: int,
        window_length: float,  # 0.005,
        max_frequency: float,  # 5000,
        dynamic_range: float,  # 90,
        n_slices: int,  # 10 ** 7,
    ) -> Optional[Spectrogram]:

        try:
            import parselmouth  # type: ignore
        except ImportError as e:
            logger.warning(e)
            return None

        start_time_sec = min(max(0, start_time_ms), len(self)) / 1000
        stop_time_sec = max(0, min(len(self), stop_time_ms)) / 1000
        visible_duration_sec = stop_time_sec - start_time_sec

        time_step = visible_duration_sec / n_slices

        spec = (
            parselmouth.Sound(self.get_path())
            .extract_part(from_time=start_time_sec, to_time=stop_time_sec)
            .to_spectrogram(
                window_length=window_length,
                maximum_frequency=max_frequency,
                time_step=time_step,
            )
        )

        with warnings.catch_warnings():
            # We filter our numpy's warnings about division by zero, since we expect
            # there to be some "padding" at the start and end of the recording with
            # decibel-level zero.  Also, numpy does the sensible thing of defining
            # `np.log10(0) := float("-inf")`, so it's not an issue for us.
            warnings.filterwarnings(
                "ignore",
                message="divide by zero encountered in log10",
                category=RuntimeWarning,
            )
            spec_arr = 10 * np.log10(np.flipud(spec.values))

        # Normalize output array
        max_magnitude = spec_arr.max()
        spec_arr = (
            (
                spec_arr.clip(max_magnitude - dynamic_range, max_magnitude)
                - max_magnitude
            )
            * -255
            / dynamic_range
        )

        return spec_arr
