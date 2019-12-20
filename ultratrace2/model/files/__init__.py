from .registry import register_loader_for_extensions_and_mime_types as __register

from .loaders import DICOMLoader
from .loaders import FLACLoader
from .loaders import MeasurementLoader
from .loaders import MP3Loader
from .loaders import OggLoader
from .loaders import TextGridLoader
from .loaders import WAVLoader


__register(
    [".dicom", ".dcm"], ["application/dicom"], DICOMLoader,
)
__register(
    [], [], FLACLoader,
)
__register(
    [], [], MeasurementLoader,
)
__register(
    [], [], MP3Loader,
)
__register(
    [], [], OggLoader,
)
__register(
    [".textgrid"], ["text/plain"], TextGridLoader,
)
__register(
    [".wav"], ["audio/x-wav", "audio/wav"], WAVLoader,
)
