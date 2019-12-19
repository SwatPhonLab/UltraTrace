import logging
import os

from typing import Dict, Sequence, FrozenSet

from .impls import Sound, Alignment, ImageSet


logger = logging.getLogger(__name__)


class FileBundle:
    def __init__(self, name: str):
        self.name = name
        self.alignment_file = Alignment()
        self.image_file = ImageSet()
        self.sound_file = Sound()

    def interpret(self, path: str):  # FIXME: add signature
        return (
            self.alignment_file.interpret(path)
            or self.image_file.interpret(path)
            or self.sound_file.interpret(path)
        )  # noqa: E126

    def has_impl(self) -> bool:
        return (
            self.alignment_file.has_impl()
            or self.image_file.has_impl()
            or self.sound_file.has_impl()
        )

    def __repr__(self):
        return f'Bundle("{self.name}",{self.alignment_file},{self.image_file},{self.sound_file})'


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

    def __init__(self, bundles: Dict[str, FileBundle]):

        self.current_bundle = None
        self.bundles: Dict[str, FileBundle] = bundles

        self.has_alignment_impl: bool = False
        self.has_image_impl: bool = False
        self.has_sound_impl: bool = False

        for filename, bundle in bundles.items():
            if not self.has_alignment_impl and bundle.alignment_file.has_impl():
                self.has_alignment_impl = True
            if not self.has_image_impl and bundle.image_file.has_impl():
                self.has_image_impl = True
            if not self.has_sound_impl and bundle.sound_file.has_impl():
                self.has_sound_impl = True

    @classmethod
    def build_from_dir(
        cls, root_path: str, extra_exclude_dirs: Sequence[str] = []
    ) -> "FileBundleList":

        # FIXME: implement `extra_exclude_dirs` as a command-line arg
        exclude_dirs = cls.exclude_dirs.copy().union(extra_exclude_dirs)

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

                if name not in bundles:
                    bundles[name] = FileBundle(name)

                if not bundles[name].interpret(filepath):
                    logger.warning(f"unrecognized filetype: {filepath}")

        return FileBundleList(bundles)
