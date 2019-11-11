import os

from collections import defaultdict
from .impls import Sound, Alignment, ImageSet
from ... import utils

class FileBundle:
    def __init__(self, name):
        self.name = name
        self.alignment_file = Alignment()
        self.image_files = ImageSet()
        self.sound_file = Sound()

    def interpret(self, path):
        return self.alignment_file.interpret(path) \
                or self.image_files.interpret(path) \
                or self.sound_file.interpret(path)

    def has_impl(self):
        return self.alignment_file.has_impl or self.image_files.has_impl or self.sound_file.has_impl

    def __repr__(self):
        return f'Bundle("{self.name}",{self.alignment_file},{self.image_files},{self.sound_file})'

class FileBundleList:
    def __init__(self, path):
        self.path = path
        self.has_alignment_impl = False
        self.has_images_impl = False
        self.has_sound_impl = False

        self.current_bundle = None
        #self.bundles = ??? # FIXME: decide on a data structure

        bundles = {}
        for path, _, filenames in os.walk(path):
            for filename in filenames:

                name, _ = os.path.splitext(filename)
                filepath_or_symlink = os.path.join(path, filename)
                filepath = os.path.realpath(filepath_or_symlink)
                if not os.path.exists(filepath):
                    utils.warn(f'unable to open "{filepath_or_symlink}" (broken symlink?)')
                    continue

                if name not in bundles:
                    bundles[name] = FileBundle(name)

                if not bundles[name].interpret(filepath):
                    utils.warn(f'unrecognized filetype: {path}')

        # FIXME: do this when we add to our data structure
        for filename, bundle in bundles.items():
            # build up self.bundles here
            if not self.has_alignment_impl and bundle.alignment_file.has_impl():
                self.has_alignment_impl = True
            if not self.has_images_impl and bundle.image_files.has_impl():
                self.has_images_impl = True
            if not self.has_sound_impl and bundle.sound_file.has_impl():
                self.has_sound_impl = True
