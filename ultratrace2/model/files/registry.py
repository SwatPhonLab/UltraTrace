import magic  # type: ignore
import os

from typing import Dict, Mapping, Optional, Sequence, Set, Type, Union

from .loaders.base import (
    FileLoaderBase,
    AlignmentFileLoader,
    ImageSetFileLoader,
    SoundFileLoader,
)


AbstractLoader = Union[
    Type[AlignmentFileLoader], Type[ImageSetFileLoader], Type[SoundFileLoader]
]

# global maps
__extension_to_loaders_map: Dict[str, Type[FileLoaderBase]] = {}
__mime_type_to_loaders_map: Dict[str, Type[FileLoaderBase]] = {}
__loader_priorities_map: Mapping[AbstractLoader, Set[int]] = {
    AlignmentFileLoader: set(),
    ImageSetFileLoader: set(),
    SoundFileLoader: set(),
}


def register_loader_for_extensions_and_mime_types(
    extensions: Sequence[str],
    mime_types: Sequence[str],
    loader_cls: Type[FileLoaderBase],
) -> None:
    """Register a loader which recognizes a file in the format indicated by the given
    extensions and MIME types.

    Parameters:
        extensions: A set of file extension, e.g. [".wav"], indicating the file format
        mime_types: A set of MIME types, e.g. ["audio/x-wav", "audio/wav"], also indicating the file format
        loader_cls: A file loader which knows how to load files with the given file extensions and MIME types
    """

    loader_type: AbstractLoader
    if issubclass(loader_cls, AlignmentFileLoader):
        loader_type = AlignmentFileLoader
    elif issubclass(loader_cls, ImageSetFileLoader):
        loader_type = ImageSetFileLoader
    elif issubclass(loader_cls, SoundFileLoader):
        loader_type = SoundFileLoader
    else:
        raise ValueError(f"Invalid loader class: {loader_cls.__name__}")
    priority = loader_cls.get_priority()
    if priority in __loader_priorities_map[loader_type]:
        raise ValueError(
            f"Cannot have duplicate priorities for loader type {loader_type.__name__}"
        )

    for extension in extensions:
        __extension_to_loaders_map[extension] = loader_cls

    for mime_type in mime_types:
        __mime_type_to_loaders_map[mime_type] = loader_cls


def get_loader_for(path: str) -> Optional[Type[FileLoaderBase]]:

    _, extension = os.path.splitext(path.lower())
    mime_type = magic.Magic(mime=True).from_file(path)
    if mime_type is None:
        # Early return since we can't possibly match anymore
        return None

    loader_cls_by_extension = __extension_to_loaders_map.get(extension, None)
    loader_cls_by_mime_type = __mime_type_to_loaders_map.get(mime_type, None)

    # NB: Use set-intersection (could potentially use set-union instead).
    if loader_cls_by_extension is None or loader_cls_by_mime_type is None:
        return None
    if loader_cls_by_extension == loader_cls_by_mime_type:
        return loader_cls_by_extension
    else:
        raise ValueError(
            f"Warning: got {loader_cls_by_extension.__name__} for {extension} and {loader_cls_by_mime_type} for {mime_type}"
        )
