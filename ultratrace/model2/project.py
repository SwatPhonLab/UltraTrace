import os

from .trace import TraceList
from .participant import ParticipantList

class Project:
    def __init__(self, path):
        if not os.path.exists(path):
            raise ValueError(f'cannot initialize project at {path}')
        self.root_path = os.path.realpath(os.path.abspath(path)) # absolute path
        #self.name = None # extract from path?
        self.traces = TraceList()
        self.participant = ParticipantList(self.root_path)

    def save(self):
        raise NotImplementedError()

    @classmethod
    def load(cls):
        raise NotImplementedError()

    def filepath(self):
        raise NotImplementedError()

    def current_trace(self):
        raise NotImplementedError()

    def current_participant(self):
        raise NotImplementedError()

    def current_bundle(self):
        raise NotImplementedError()

    def current_frame(self):
        raise NotImplementedError()
