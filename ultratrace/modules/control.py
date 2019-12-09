from .base import Module
import tkinter as tk

class Control(Module):
    def __init__(self, app):
        self.app.bind('<Control-z>' if util.get_platform() == 'Linux' else '<Command-z>', self.undo )
        self.app.bind('<Control-Z>' if util.get_platform() == 'Linux' else '<Command-Z>', self.redo )
        self.frame = tk.Frame(self.app.LEFT)#, pady=7)
        self.frame.grid( row=5 )
        self.undoBtn = tk.Button(self.frame, text='Undo', command=self.undo, takefocus=0)
        self.redoBtn = tk.Button(self.frame, text='Redo', command=self.redo, takefocus=0)
    def updateButtons(self):
        self.undoBtn['state'] = 'normal' if len(self.uStack) else 'disabled'
        self.redoBtn['state'] = 'normal' if len(self.rStack) else 'disabled'
    def grid(self):
        self.undoBtn.grid(row=0, column=0)
        self.redoBtn.grid(row=0, column=1)
    def grid_remove(self):
        self.undoBtn.grid_remove()
        self.redoBtn.grid_remove()
