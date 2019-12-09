from .base import Module
from ..widgets import ZoomFrame
import tkinter as tk

class Dicom(Module):
    def __init__(self, app):
        self.frame_holder = tk.Frame(self.app.LEFT)
        self.frame_holder.grid( row=2 )
        self.frame = tk.Frame(self.frame_holder)
        self.frame.pack(expand=True)
        self.method = tk.StringVar(self.app)
        self.zframe = widgets.ZoomFrame(self.app.RIGHT, 1.3, app)
        self.zoomResetBtn = tk.Button(self.app.LEFT, text='Reset image', command=self.zoomReset, takefocus=0)
        self.app.bind('<Control-0>' if util.get_platform() == 'Linux' else '<Command-0>', self.zoomReset )

    def zoomReset(self, fromButton=False):
        self.zframe.resetCanvas()

    def update(self, _frame=None):
        self.zframe.setImage(self.reader.getFrame(_frame or self.app.frame))

    def load(self, event=None):
        self.loadBtn['state'] = 'disabled'

    def chooseMethod(self, event=None):
        self.zframe.resetImageDimensions()
        self.loadBtn['state'] = 'disabled' if self.reader.loaded else 'normal'

    def reset(self):
        self.zframe.shown = False
        self.frame.destroy()
        self.frame = tk.Frame(self.frame_holder)
        self.frame.pack(expand=True)
        self.methodMenu = tk.OptionMenu(self.frame, self.method, *[x.label for x in READERS[self.mode]] or ['[no ultrasound]'], command=self.chooseMethod)
        self.methodMenu.grid(row=0)
        self.loadBtn = tk.Button(self.frame, text='Load frames', command=self.load, takefocus=0)
        self.loadBtn.grid(row=1)

    def grid(self):
        self.app.framesHeader.grid(   row=0 )
        self.app.framesPrevBtn.grid(      row=0, column=0 )
        self.app.framesEntryText.grid( row=0, column=1 )
        self.app.framesEntryBtn.grid(  row=0, column=2 )
        self.app.framesNextBtn.grid(  row=0, column=3 )
        self.zoomResetBtn.grid( row=7 )
        self.app.Control.grid()

    def grid_remove(self):
        self.app.framesHeader.grid_remove()
        self.app.framesPrevBtn.grid_remove()
        self.app.framesEntryText.grid_remove()
        self.app.framesEntryBtn.grid_remove()
        self.app.framesNextBtn.grid_remove()
        self.zoomResetBtn.grid_remove()
        self.app.Control.grid_remove()
