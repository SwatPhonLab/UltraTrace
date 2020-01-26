import logging
import os

from typing import Dict, FrozenSet, Mapping, Optional, Sequence, Type

from .loaders.base import (
    AlignmentFileLoader,
    ImageSetFileLoader,
    SoundFileLoader,
    FileLoaderBase,
    FileLoadError,
)
from .registry import get_loader_for


logger = logging.getLogger(__name__)


class FileBundle:
    def __init__(
        self,
        name: str,
        alignment_file: Optional[AlignmentFileLoader] = None,
        image_set_file: Optional[ImageSetFileLoader] = None,
        sound_file: Optional[SoundFileLoader] = None,
    ):
        self.name = name
        self.alignment_file = alignment_file
        self.image_set_file = image_set_file
        self.sound_file = sound_file

    def has_impl(self) -> bool:
        return any(
            f is not None
            for f in [self.alignment_file, self.image_set_file, self.sound_file]
        )

    def get_alignment_file(self) -> Optional[AlignmentFileLoader]:
        return self.alignment_file

    def set_alignment_file(self, alignment_file: AlignmentFileLoader) -> None:
        if self.alignment_file is not None:
            logger.warning("Overwriting existing alignment file")
        self.alignment_file = alignment_file

    def get_image_set_file(self) -> Optional[ImageSetFileLoader]:
        return self.image_set_file

    def set_image_set_file(self, image_set_file: ImageSetFileLoader) -> None:
        if self.image_set_file is not None:
            logger.warning("Overwriting existing image-set file")
        self.image_set_file = image_set_file

    def get_sound_file(self) -> Optional[SoundFileLoader]:
        return self.sound_file

    def set_sound_file(self, sound_file: SoundFileLoader) -> None:
        if self.sound_file is not None:
            logger.warning("Overwriting existing sound file")
        self.sound_file = sound_file

    def __repr__(self):
        return f'Bundle("{self.name}",{self.alignment_file},{self.image_set_file},{self.sound_file})'

    def __eq__(self, other):
        return (
            self.name == other.name
            and self.alignment_file == other.alignment_file
            and self.image_set_file == other.image_set_file
            and self.sound_file == other.sound_file
        )


class FileBundleList:

    exclude_dirs: FrozenSet[str] = frozenset(
        [
            ".git",
            "node_modules",
            "__pycache__",
            ".ultratrace",
            # FIXME: add more ignoreable dirs
        ]
    )

    def __init__(self, bundles: Mapping[str, FileBundle]):

        self.current_bundle = None
        self.bundles: Mapping[str, FileBundle] = bundles

        self.has_alignment_impl: bool = False
        self.has_image_set_impl: bool = False
        self.has_sound_impl: bool = False

        for bundle in bundles.values():
            self.has_alignment_impl |= bundle.alignment_file is not None
            self.has_image_set_impl |= bundle.image_set_file is not None
            self.has_sound_impl |= bundle.sound_file is not None

    @classmethod
    def build_from_dir(
        cls, root_path: str, extra_exclude_dirs: Sequence[str] = []
    ) -> "FileBundleList":

        assert os.path.exists(root_path)  # should have been validated by Project

        # FIXME: implement `extra_exclude_dirs` as a command-line arg
        exclude_dirs = cls.exclude_dirs.union(extra_exclude_dirs)

        bundles: Dict[str, FileBundle] = {}

        # NB: `topdown=True` increases runtime cost from O(n) -> O(n^2), but it allows us to
        #     modify `dirs` in-place so that we can skip certain directories.  For more info,
        #     see https://stackoverflow.com/questions/19859840/excluding-directories-in-os-walk
        for path, dirs, filenames in os.walk(root_path, topdown=True):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for filename in filenames:

                name, _ = os.path.splitext(filename)
                filepath_or_symlink = os.path.join(path, filename)
                filepath = os.path.realpath(filepath_or_symlink)
                if not os.path.exists(filepath):
                    logger.warning(
                        f'unable to open "{filepath_or_symlink}" (broken symlink?)'
                    )
                    continue

                file_loader: Optional[Type[FileLoaderBase]] = get_loader_for(filepath)
                if file_loader is None:
                    logger.warning(f"unrecognized filetype: {filepath}")
                    continue

                if name not in bundles:
                    bundles[name] = FileBundle(name)

                try:
                    loaded_file = file_loader.from_file(filepath)
                    if loaded_file is not None:
                        if isinstance(loaded_file, AlignmentFileLoader):
                            bundles[name].set_alignment_file(loaded_file)
                        elif isinstance(loaded_file, ImageSetFileLoader):
                            bundles[name].set_image_set_file(loaded_file)
                        elif isinstance(loaded_file, SoundFileLoader):
                            bundles[name].set_sound_file(loaded_file)
                except FileLoadError as e:
                    logger.error(e)

        return cls(bundles)
