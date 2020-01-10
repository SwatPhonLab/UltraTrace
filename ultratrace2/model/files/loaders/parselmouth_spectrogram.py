from PIL import Image  # type: ignore

import logging
import numpy as np
import parselmouth  # type: ignore
import pickle
import warnings

from .base import FileLoadError, SoundFileLoader, SpectrogramFileLoader


logger = logging.getLogger(__name__)


class ParselmouthLoader(SpectrogramFileLoader):
    def get_path(self) -> str:
        return self._path

    def set_path(self, path) -> None:
        self._path = path

    def __init__(self, path: str, pm_sound: parselmouth.Sound):
        self.set_path(path)
        self.pm_sound = pm_sound

    def save(self) -> None:
        with open(self.get_path(), "wb") as fp:
            pickle.dump(self.pm_sound.as_array(), fp)
            logger.debug(f"Wrote ParselmouthLoader to disk: {self.get_path()}")

    @classmethod
    def from_file(cls, path: str) -> "ParselmouthLoader":
        try:
            with open(path, "rb") as fp:
                pm_sound = parselmouth.Sound(pickle.load(fp))
            return cls(path, pm_sound)
        except Exception as e:
            raise FileLoadError from e

    load = from_file  # alias

    @classmethod
    def from_sound_file(cls, sound_file: SoundFileLoader) -> "ParselmouthLoader":
        try:
            pm_sound = parselmouth.Sound(sound_file.get_path())
            pm_path = f"{sound_file.get_path()}.pmpkl"
            pm = cls(pm_path, pm_sound)
            pm.save()
            return pm
        except Exception as e:
            raise FileLoadError from e

    def get_image(
        self,
        start_time_ms: int,
        stop_time_ms: int,
        window_length: float,  # 0.005,
        max_frequency: float,  # 5000,
        dynamic_range: float,  # 90,
        n_slices: int,  # 10 ** 7,
    ) -> Image.Image:

        # NB: need to do validation of *_time_ms BEFORE calling
        start_time_sec = start_time_ms / 1000
        stop_time_sec = stop_time_ms / 1000
        visible_duration_sec = stop_time_sec - start_time_sec

        time_step = visible_duration_sec / n_slices

        spec = self.pm_sound.extract_part(
            from_time=start_time_sec, to_time=stop_time_sec
        ).to_spectrogram(
            window_length=window_length,
            maximum_frequency=max_frequency,
            time_step=time_step,
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

        return Image.fromarray(spec_arr).convert("RGB")
