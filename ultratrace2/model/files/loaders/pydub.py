from typing import Optional

import logging
import numpy as np
import pydub  # type: ignore

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
        start_time: int,
        stop_time: int,
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

        start_time = max(0, start_time)
        stop_time = min(len(self), stop_time)
        visible_duration = stop_time - start_time

        time_step = visible_duration / n_slices

        sound_clip = parselmouth.Sound(self.get_path()).extract_part(
            from_time=start_time, to_time=stop_time
        )

        spec = sound_clip.to_spectrogram(
            window_length=window_length,
            maximum_frequency=max_frequency,
            time_step=time_step,
        )

        spec_arr = 10 * np.log10(np.flipud(spec.values))
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
