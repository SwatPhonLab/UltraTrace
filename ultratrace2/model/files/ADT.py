import logging
import os

from abc import ABC, abstractmethod
from collections import OrderedDict
from magic import Magic  # type: ignore
from typing import ClassVar, Dict, Optional, Sequence, Type


logger = logging.getLogger(__name__)


class FileLoadError(Exception):
    pass


class TypedFile(ABC):

    preferred_impls = ClassVar[Sequence["TypedFileImpl"]]

    impls: Dict[Type["TypedFileImpl"], Optional["TypedFileImpl"]]
    impl: Optional["TypedFileImpl"]

    def __new__(cls):
        cls.impls = OrderedDict()
        for impl_type in cls.preferred_impls:
            cls.impls[impl_type] = None
        return super().__new__(cls)

    def __init__(self):
        self.impl = None

    def has_impl(self) -> bool:
        return self.impl is not None

    def interpret(self, path: str) -> bool:
        mimetype = Magic(mime=True).from_file(path)
        _, extension = os.path.splitext(path.lower())
        recognized = False
        for Impl in self.preferred_impls:
            if Impl.recognizes(mimetype, extension):
                recognized = True
                if self.impl is not None:
                    logger.error(
                        f"cannot parse {path}: previous {type(Impl).__name__} was: {self.impl.path}, skipping..."
                    )
                    continue
                self.impl = Impl(path)
                return True
        return recognized

    def data(self):  # FIXME: add signature
        if self.impl is None:
            raise ValueError("cannot load: no implementation found")
        try:
            self.impl.data()
        except FileLoadError as e:
            logger.error(f"unable to load {self.impl}: {e}")
            self.impl = None  # FIXME: is this sane behavior?

    def __repr__(self):
        return f"{type(self).__name__}({self.impl})"


class TypedFileImpl(ABC):

    mimetypes: ClassVar[Sequence[str]]
    extensions: ClassVar[Sequence[str]]

    def __init__(self, path: str):
        self.path = path
        self._data = None

    def data(self):  # FIXME: add signature
        # lazy load
        if self._data is None:
            self.load()
        return self._data

    @abstractmethod
    def load(self):  # should throw FileLoadError if something went wrong
        pass

    @classmethod
    def recognizes(cls, mimetype: str, extension: str) -> bool:
        return mimetype in cls.mimetypes or extension in cls.extensions

    def __repr__(self):
        return f'{type(self).__name__}("{self.path}")'
