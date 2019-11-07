import utils

from io_ import IO
from gui import GUI
from model import Model

class App:
    def __init__(self, args):

        self.io = IO(self, args)
        self.model = Model(self, args)
        self.gui = GUI(self, args)

    def main(self):
        #self.gui.mainloop()
        self.gui.quit()


