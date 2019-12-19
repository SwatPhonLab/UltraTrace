import mimetypes
import os

from collections import defaultdict
from typing import DefaultDict, Optional, Sequence, Set, Type

from .loaders.base import FileLoaderBase


# global maps
__extension_to_loaders_map: DefaultDict[str, Set[Type[FileLoaderBase]]] = defaultdict(
    set
)
__mime_type_to_loaders_map: DefaultDict[str, Set[Type[FileLoaderBase]]] = defaultdict(
    set
)


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

    global __extension_to_loaders_map
    global __mime_type_to_loaders_map

    for extension in extensions:
        __extension_to_loaders_map[extension].add(loader_cls)

    for mime_type in mime_types:
        __mime_type_to_loaders_map[mime_type].add(loader_cls)


def get_loader_for(path: str) -> Optional[Type[FileLoaderBase]]:

    global __extension_to_loaders_map
    global __mime_type_to_loaders_map

    _, extension = os.path.splitext(path.lower())
    mime_type, _ = mimetypes.guess_type(path)
    if mime_type is None:
        # Early return since we can't possibly match anymore
        return None

    loader_clses_by_extension = __extension_to_loaders_map[extension]
    loader_clses_by_mime_type = __mime_type_to_loaders_map[mime_type]

    # NB: Use set-intersection (could potentially use set-union instead).
    loader_clses = loader_clses_by_extension & loader_clses_by_mime_type

    if len(loader_clses) == 0:
        return None
    elif len(loader_clses) == 1:
        return loader_clses.pop()
    else:
        raise NotImplementedError(
            f"Found multiple Loaders for path '{path}': {','.join(map(str, loader_clses))}"
        )
