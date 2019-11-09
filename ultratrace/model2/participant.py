import os

from .files.bundle import FileBundleList
from .. import utils

class Participant:
    def __init__(self, path: str):
        print(f'\nParticipant.__init__({path})')
        self.path = path
        #self.name = None # extract from path
        self.is_visible = True
        self.files = FileBundleList(path)

class ParticipantList:
    def __init__(self, root_path):
        self.has_alignment_impl = False
        self.has_image_impl = False
        self.has_sound_impl = False

        self.current_participant = None
        #self.participants = ??? # FIXME: decide on a data structure

        participants = []
        for name in os.listdir(root_path):
            path = os.path.join(root_path, name)
            if not os.path.isdir(path):
                utils.warn('encountered unexpected regular file:', path)
                continue
            participants.append(Participant(path))

        # FIXME: do this when we add to our data structure
        for participant in participants:
            if not self.has_alignment_impl and participant.files.has_alignment_impl:
                self.has_alignment_impl = True
            if not self.has_image_impl and participant.files.has_image_impl:
                self.has_image_impl = True
            if not self.has_sound_impl and participant.files.has_sound_impl:
                self.has_sound_impl = True
