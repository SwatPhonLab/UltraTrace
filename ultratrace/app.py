import utils

from model import Model
from gui import GUI

class App:
    def __init__(self, args):

        self.model = Model(self, args)
        self.gui = GUI(self, args)

        self.gui.mainloop()


