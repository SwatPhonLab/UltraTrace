from .base import Module
from .. import util
from ..util.logging import *
from ..util.framereader import *

import os
import PIL

from tkinter import *

LIBS_INSTALLED = False

try:
    from ..widgets import ZoomFrame
    import numpy as np
    import pydicom # pydicom
    LIBS_INSTALLED = True
except ImportError as e:
    warn(e)

class DicomModule(Module):
    def __init__(self, app):
        info( ' - initializing module: Dicom')

        self.app = app

        if LIBS_INSTALLED:
            # grid load button
            self.frame_holder = Frame(self.app.LEFT)#, pady=7)
            self.frame_holder.grid( row=2 )
            self.frame = Frame(self.frame_holder)
            self.frame.pack(expand=True)
            self.method = StringVar(self.app)
            self.mode = None
            self.reader = None

            # zoom frame (contains our tracing canvas)
            self.zframe = ZoomFrame(self.app.RIGHT, 1.3, app)

            # reset zoom button
            self.zoomResetBtn = Button(self.app.LEFT, text='Reset image', command=self.zoomReset, takefocus=0)#, pady=7 )

            # reset zoom keyboard shortcut
            if util.get_platform() == 'Linux':
                self.app.bind('<Control-0>', self.zoomReset )
            else: self.app.bind('<Command-0>', self.zoomReset )
            self.reset()

    def zoomReset(self, fromButton=False):
        '''
        reset zoom frame canvas and rebind it
        '''
        if self.isLoaded():
            # creates a new canvas object and we redraw everything to it
            self.zframe.resetCanvas()
            # self.zframe.canvas.bind('<Button-1>', self.app.onClickZoom )
            # self.zframe.canvas.bind('<ButtonRelease-1>', self.app.onRelease )
            # self.zframe.canvas.bind('<Motion>', self.app.onMotion )

            # we want to go here only after a button press
            if fromButton: self.app.framesUpdate()

    def update(self, _frame=None):
        '''
        change the image on the zoom frame
        '''
        if self.reader and self.reader.loaded:
            self.zframe.setImage(self.reader.getFrame(_frame or self.app.frame))

    def load(self, event=None):
        '''
        brings a dicom file into memory if it exists
        '''
        if LIBS_INSTALLED:
            if self.reader and not self.reader.loaded:
                self.reader.load()
                self.app.frame = 1
                self.update()
            self.loadBtn['state'] = DISABLED

    def chooseMethod(self, event=None):
        if self.mode:
            cls = LABEL_TO_READER[self.mode][self.method.get()]
            if self.mode == 'dicom':
                self.reader = cls(self.app.Data.unrelativize(self.app.Data.getFileLevel('.dicom')))
            elif self.mode == 'ult':
                ult = self.app.Data.unrelativize(self.app.Data.getFileLevel('.ult'))
                meta = self.app.Data.unrelativize(self.app.Data.getFileLevel('US.txt'))
                self.reader = cls(uls, meta)
            self.zframe.resetImageDimensions()
            if self.reader.loaded:
                self.loadBtn['state'] = DISABLED
                self.update()
            else:
                self.loadBtn['state'] = NORMAL

    # @profile
    def process(self):
        '''
        perform the dicom->PNG operation
        '''
        self.frametime = self.dicom.get('FrameTime')
        self.numframes = self.dicom.get('NumberOfFrames')
        self.app.Data.setFileLevel('FrameTime', self.frametime)
        self.app.Data.setFileLevel('NumberOfFrames', self.numframes)

    def isLoaded(self):
        return self.reader and self.reader.loaded

    def getFrames(self, framenums):
        return [self.reader.getFrame(int(x)) for x in framenums]

    def reset(self):
        '''
        new files should default to not showing dicom unless it has already been processed
        '''
        # hide frame navigation widgets
        # self.grid_remove()

        self.zframe.shown = False
        self.frame.destroy()
        self.frame = Frame(self.frame_holder)
        self.frame.pack(expand=True)
        self.reader = None

        if self.app.Data.getFileLevel('.dicom'):
            self.mode = 'dicom'
        elif self.app.Data.getFileLevel('.ult'):
            self.mode = 'ult'
        else:
            self.mode = None

        self.methodMenu = OptionMenu(self.frame, self.method, *[x.label for x in READERS[self.mode]], command=self.chooseMethod)
        self.methodMenu.grid(row=0)
        self.loadBtn = Button(self.frame, text='Load frames', command=self.load, takefocus=0)
        self.loadBtn.grid(row=1)

    def grid(self):
        '''
        Grid frame navigation, zoom reset, and Control (Undo/Redo) widgets
        '''
        self.app.framesHeader.grid(   row=0 )
        self.app.framesPrevBtn.grid(      row=0, column=0 )
        self.app.framesEntryText.grid( row=0, column=1 )
        self.app.framesEntryBtn.grid(  row=0, column=2 )
        self.app.framesNextBtn.grid(  row=0, column=3 )
        self.zoomResetBtn.grid( row=7 )
        self.app.Control.grid()

    def grid_remove(self):
        '''
        Remove widgets from grid
        '''
        self.app.framesHeader.grid_remove()
        self.app.framesPrevBtn.grid_remove()
        self.app.framesEntryText.grid_remove()
        self.app.framesEntryBtn.grid_remove()
        self.app.framesNextBtn.grid_remove()
        self.zoomResetBtn.grid_remove()
        self.app.Control.grid_remove()
