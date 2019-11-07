from .undo import UndoManager
from .metadata import Metadata

class Model:
    def __init__(self, app, args):

        self.app = app

        self.undo_mgr = UndoManager(app, args)
        self.metadata = Metadata(app, args)

