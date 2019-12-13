import os
import platform

from .. import utils

try:
    from ttkthemes import ThemedTk
except ImportError:
    utils.warn('Unable to load themes')
    from tkinter import Tk as ThemedTk

def get_theme(name):
    if name is not None:
        return name

    if platform.system() == 'Linux':
        try:

            import xrp

            Xresources_path = os.path.join(os.environ['HOME'], '.Xresources')
            if os.path.exists(Xresources_path):
                Xresources = xrp.parse_file(Xresources_path)
                if '*TtkTheme' in Xresources.resources:
                    return Xresources.resources['*TtkTheme']
                if '*TkTheme' in Xresources.resources:
                    return Xresources.resources['*TkTheme']
                return 'clam'

        except Exception as e:
            utils.warn('Error loading themes: ' + str(e))

    return None
