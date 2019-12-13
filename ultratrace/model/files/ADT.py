import os

from abc import ABC, abstractmethod
from collections import OrderedDict
from magic import Magic
from ... import utils

class FileLoadError(Exception):
    pass

class TypedFile(ABC):

    @property
    @staticmethod
    @abstractmethod
    def preferred_impls() -> list:
        pass

    def __new__(cls):
        cls.impls = OrderedDict()
        for impl_type in cls.preferred_impls:
            cls.impls[impl_type] = None
        return super().__new__(cls)

    def __init__(self):
        self.impl = None

    def has_impl(self) -> bool:
        return self.impl is not None

    def interpret(self, path):
        mimetype = Magic(mime=True).from_file(path)
        _, extension = os.path.splitext(path.lower())
        recognized = False
        for Impl in self.preferred_impls:
            if Impl.recognizes(mimetype, extension):
                recognized = True
                if self.impl is not None:
                    utils.error(f'cannot parse {path}: previous {Impl.__name__} was: {self.impl.path}, skipping...')
                    continue
                self.impl = Impl(path)
                return True
        return recognized

    def data(self):
        if self.impl is None:
            raise ValueError('cannot load: no implementation found')
        try:
            self.impl.data()
        except FileLoadError as e:
            utils.error(f'unable to load {self.impl}: {e}')
            self.impl = None

    def __repr__(self):
        return f'{type(self).__name__}({self.impl})'

class TypedFileImpl(ABC):

    @property
    @staticmethod
    @abstractmethod
    def mimetypes():
        pass

    @property
    @staticmethod
    @abstractmethod
    def extensions():
        pass

    def __init__(self, path):
        self.path = path
        self._data = None

    def data(self):
        # lazy load
        if self._data is None:
            self.load()
        return self._data

    @abstractmethod
    def load(self): # should throw FileLoadError if something went wrong
        pass

    @classmethod
    def recognizes(cls, mimetype, extension):
        return mimetype in cls.mimetypes or extension in cls.extensions

    def __repr__(self):
        return f'{type(self).__name__}("{self.path}")'
