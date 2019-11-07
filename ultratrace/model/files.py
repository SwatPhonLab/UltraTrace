import os
import utils

from magic import Magic

class FilesList:
    def __init__(self, root):

        self.files = []
        self.hashes = set() # for quick lookups

        for path, _dirs, files in os.walk(root):
            for f in files:

                filepath_or_symlink = os.path.join(path, f)
                filepath = os.path.realpath(filepath_or_symlink)
                if not os.path.exists(filepath):
                    utils.warn(f'unable to open "{filepath_or_symlink}" (broken symlink?)')
                    continue

                file_ = File(filepath)

                if file_.filetype == Unknown:
                    continue

                if file_ in self:
                    continue

                self.add(file_)

        if len(self) == 0:
            raise ValueError(f'no supported files found at "{root}"')

    def __len__(self):
        return len(self.files)

    def __iter__(self):
        for f in self.files:
            yield f

    def __contains__(self, file_):
        return file_ in self.hashes

    def __getitem__(self, i):
        if len(self) == 0:
            raise IndexError('cannot __getitem__ from empty FilesList')
        return self.files[i]

    def add(self, file_):
        if file_ in self:
            utils.warn('skipping file: already present', file_)
            return
        if len(self):
            self[-1]._next = file_
            file_._prev = self[-1]
        self.hashes.add(file_)
        self.files.append(file_)

    def head(self):
        return self[0]

    def tail(self):
        return self[-1]

    def __repr__(self):
        return f'[{",".join(map(repr, self))}]'

class File:
    def __init__(self, path):

        self._prev = None
        self._next = None

        self.path = path
        self.filetype = File.guess_filetype(path)
        self.is_processed = False
        self.offset = None

    @staticmethod
    def guess_filetype(filepath):
        mimetype = Magic(mime=True).from_file(filepath)
        _, extension = os.path.splitext(filepath.lower())
        for filetype in supported_filetypes:
            if filetype.matches(mimetype, extension):
                return filetype
        return Unknown

    def next(self):
        if self._next is None:
            raise IndexError('cannot get next()')
        return self._next

    def prev(self):
        if self._prev is None:
            raise IndexError('cannot get prev()')
        return self._prev

    def __repr__(self):
        return f'{self.filetype.__name__}File("{self.path}")'

    def __hash__(self):
        return hash(self.path)

class FileType:
    mimetypes = []
    extensions = []

    @classmethod
    def matches(cls, mimetype, extension):
        return mimetype in cls.mimetypes or extension in cls.extensions

class Unknown(FileType):
    @classmethod
    def matches(cls, mimetype, extension):
        return True

class WAV(FileType):
    mimetypes = ['audio/x-wav', 'audio/wav']
    extensions = ['wav']

class FLAC(FileType):
    mimetypes = ['audio/x-flac', 'audio/flac']
    extensions = ['flac']

class DICOM(FileType):
    mimetypes = ['application/dicom']
    extensions = ['.dicom', '.dcm']

class TextGrid(FileType):
    mimetypes = ['text/plain']
    extensions = ['.textgrid']

    @classmethod
    def matches(cls, mimetype, extension):
        return mimetype in cls.mimetypes and extension in cls.extensions

class Measurement(FileType):
    mimetypes = ['text/plain', 'application/json']
    extensions = ['.measurement']

    @classmethod
    def matches(cls, mimetype, extension):
        return mimetype in cls.mimetypes and extension in cls.extensions

class PNG(FileType):
    mimetypes = ['image/png']
    extensions = ['.png']

supported_filetypes = [ WAV, FLAC, DICOM, TextGrid, PNG ]

