from tkinter.filedialog import askdirectory as choose_dir

from . import utils
from .gui import GUI
from .model.project import Project

class App:
    def __init__(self, args):

        if args.path is None:
            path = choose_dir()
            if not path:
                raise ValueError('You must choose a directory to open')
        else:
            path = args.path

        self.project = Project(path)
        self.gui = GUI(self, theme=args.theme)

    def main(self):
        pass
        #self.gui.mainloop()
        #self.gui.quit()


