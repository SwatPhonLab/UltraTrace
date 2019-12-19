import logging
import os

from typing import Dict, FrozenSet, Optional, Sequence, Type

from .adt import AlignmentFile, ImageSetFile, SoundFile, TypedFile


logger = logging.getLogger(__name__)


class FileBundle:
    def __init__(
        self,
        name: str,
        alignment_file: Optional[AlignmentFile] = None,
        image_file: Optional[ImageSetFile] = None,
        sound_file: Optional[SoundFile] = None,
    ):
        self.name = name
        self.alignment_file = alignment_file
        self.image_file = image_file
        self.sound_file = sound_file

    def has_impl(self) -> bool:
        return any(
            f is not None
            for f in [self.alignment_file, self.image_file, self.sound_file]
        )

    def set_alignment_file(self, alignment_file: AlignmentFile) -> None:
        self.alignment_file = alignment_file

    def set_image_file(self, image_file: ImageSetFile) -> None:
        self.image_file = image_file

    def set_sound_file(self, sound_file: SoundFile) -> None:
        self.sound_file = sound_file

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

        for bundle in bundles.values():
            self.has_alignment_impl |= bundle.alignment_file is not None
            self.has_image_impl |= bundle.image_file is not None
            self.has_sound_impl |= bundle.sound_file is not None

    @classmethod
    def build_from_dir(
        cls, root_path: str, extra_exclude_dirs: Sequence[str] = []
    ) -> "FileBundleList":

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

                impl_cls = guess_file_type(filepath)
                if impl_cls is None:
                    logger.warning(f"unrecognized filetype: {filepath}")
                    continue

                if name not in bundles:
                    bundles[name] = FileBundle(filepath)

                file_impl = impl_cls(filepath)
                if isinstance(file_impl, AlignmentFile):
                    bundles[name].set_alignment_file(file_impl)
                elif isinstance(file_impl, ImageSetFile):
                    bundles[name].set_image_file(file_impl)
                elif isinstance(file_impl, SoundFile):
                    bundles[name].set_sound_file(file_impl)

        return cls(bundles)


def guess_file_type(path: str) -> Optional[Type[TypedFile]]:
    raise NotImplementedError()
