import os
import pickle
import utils

from collections import defaultdict
from .files import FilesList

METADATA_FILENAME = '.ultratrace.pickle'

class Metadata:
    def __init__(self, app, args):

        self.app = app

        if args.path is None:
            self.path = app.io.get_directory()
        else:
            self.path = args.path

        if os.path.exists(self.path):
            try:
                self = Metadata.load(self.get_md_path())
            except Exception as e:
                utils.warn('failed loading metadata', e)
                self.create_new()
        else:
            self.create_new()

    def get_md_path(self):
        return os.path.join(self.path, METADATA_FILENAME)

    @staticmethod
    def load(path):
        utils.debug('reading metadata from:', path)
        with open(path, 'rb') as fp:
            return pickle.load(fp)

    def save(self):
        with open(self.get_md_path(), 'wb') as fp:
            pickle.dump(self, fp)

    def create_new(self):

        utils.debug('creating new metadata file at:', self.path)

        self.project_root = self.path
        self.files = FilesList(self.path)
        self.traces = TracesList()

