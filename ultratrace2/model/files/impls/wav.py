from ..adt import TypedFile


class WAV(TypedFile):
    mimetypes = ["audio/x-wav", "audio/wav"]
    extensions = ["wav"]
