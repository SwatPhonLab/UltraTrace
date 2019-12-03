from .base import Module
from .. import util
from ..util.logging import *

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
    '''
    This module wraps app interaction with dicom data.  The first time executing a
    program for which we find relevant dicom files, the user will have to `Load DICOM,`
    which iterates over each frame of the dicom file and copies it to a folder in PNG
    format.

    advantages (over loading each frame as a one-off image):
        - avoid weird inconsistencies in trying to build PIL Images directly from arrays
        - avoid unnecessary direct interaction with the (usually massive and therefore
            painfully slow) dicom files

    drawbacks:
        - VERY slow upfront operation to do the dicom extraction (3m56s on my dev machine)
        - a tiny amount of extra storage (for comparison, 1045-frame RGB dicom file
            from a test dataset uses 1.5GB and the corresponding PNG files use )
    '''
    def __init__(self, app):
        info( ' - initializing module: Dicom')

        self.app = app
        self.isLoaded = False

        if LIBS_INSTALLED:
            # grid load button
            self.frame = Frame(self.app.LEFT)#, pady=7)
            self.frame.grid( row=2 )
            self.loadBtn = Button(self.frame, text='Load DICOM', command=self.process, takefocus=0)
            self.loadBtn.grid()

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
        if self.isLoaded:
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
        if self.isLoaded:
            image = self.app.Data.getPreprocessedDicom() if _frame==None else self.app.Data.getPreprocessedDicom(_frame=_frame)
            image = PIL.Image.open( image )
            self.zframe.setImage( image )

    def load(self, event=None):
        '''
        brings a dicom file into memory if it exists
        '''
        if LIBS_INSTALLED:
            # don't execute if dicom already loaded correctly
            if self.isLoaded == False:

                processed = self.app.Data.getFileLevel( 'processed' )
                # debug(os.path.exists(self.app.Data.unrelativize(self.app.Data.getFileLevel( 'processed' )['1'])))
                if processed == None:
                    return self.process()
                # elif :
                #   self.process()
                # else:
                #   self.app.frames = len(processed)

                # reset variables
                self.app.frame = 1
                self.isLoaded = True

                # update widgets
                self.frame.grid_remove()
                self.loadBtn.grid_remove()
                self.grid()

    # @profile
    def process(self):
        '''
        perform the dicom->PNG operation
        '''
        info( 'Reading DICOM data ...', end='\r' )

        if self.isLoaded == False:
            try:
                dicomfile = self.app.Data.getFileLevel( '.dicom' )
                self.dicom = dicom.read_file( self.app.Data.unrelativize(dicomfile) )

            except dicom.errors.InvalidDicomError:
                error( 'Unable to read DICOM file: %s' % dicomfile )
                return False

        pixels = self.dicom.pixel_array # np.array
        self.frametime = self.dicom.get('FrameTime')
        self.numframes = self.dicom.get('NumberOfFrames')
        self.app.Data.setFileLevel('FrameTime', self.frametime)
        self.app.Data.setFileLevel('NumberOfFrames', self.numframes)

        # check encoding, manipulate array if we need to
        if len(pixels.shape) == 3:      # greyscale
            RGB = False
            frames, rows, columns = pixels.shape
        elif len(pixels.shape) == 4:    # RGB-encoded
            RGB = True
            if pixels.shape[0] == 3:    # handle RGB-first
                rgb, frames, rows, columns = pixels.shape
            else:                       # and RGB-last
                frames, rows, columns, rgb = pixels.shape
            pixels = pixels.reshape([ frames, rows, columns, rgb ])

        processedData = {}

        # write to a special directory
        outputpath = os.path.join(
            # self.app.Data.getTopLevel('path'),
            os.path.abspath(self.app.Data.path),
            self.app.Data.getFileLevel('name')+'_dicom_to_png' )
        if os.path.exists( outputpath ) == False:
            os.mkdir( outputpath )
        rel_outputpath = os.path.relpath(outputpath,start=self.app.Data.path)
        # debug(self.app.Data.getFileLevel('name'))
        # grab one frame at a time to write (and provide a progress indicator)
        printProgressBar(0, frames, prefix = 'Processing:', suffix = 'complete')
        for f in range( frames ):

            printProgressBar(f+1, frames, prefix = 'Processing:', suffix = ('complete (%d of %d)' % (f+1,frames)))

            arr = pixels[ f,:,:,: ] if RGB else pixels[ f,:,: ]
            img = PIL.Image.fromarray( arr )

            outputfilename = '%s_frame_%04d.png' % ( os.path.basename(self.app.Data.getFileLevel('name')), f+1 )
            outputfilepath = os.path.join( rel_outputpath, outputfilename )
            # debug(outputfilepath)
            img.save( os.path.join(self.app.Data.path,outputfilepath), format='PNG', compress_level=1 )

            # keep track of all the processing we've finished
            # debug(os.path.join(outputpath,outputfilename))
            processedData[ str(f+1) ] = outputfilepath
        # debug(processedData)
        self.app.Data.setFileLevel( 'processed', processedData )
        self.app.lift()
        self.load()
        self.app.update()
        self.app.framesUpdate()

    # an attempt at making things parallel, but we get the following error:
    # _pickle.PicklingError: Could not pickle the task to send it to the workers.

    #   #for f in range(frames):
    #   Parallel(n_jobs=2)(delayed(self.writeTempImage)(f, frames, outputpath, RGB, pixels) for f in range(frames))
    #
    #
    #   self.app.Data.setFileLevel( 'processed', self.processedData )
    #   self.app.lift()
    #   self.load()
    #
    # def writeTempImage(self, f, frames, outputpath, RGB, pixels):
    #
    #   #printProgressBar(f+1, frames, prefix = 'Processing:', suffix = ('complete (%d of %d)' % (f+1,frames)))
    #
    #   arr = pixels[ f,:,:,: ] if RGB else pixels[ f,:,: ]
    #   img = Image.fromarray( arr )
    #
    #   outputfilename = '%s_frame_%04d.png' % ( self.app.Data.getFileLevel('name'), f )
    #   outputfilepath = os.path.join( outputpath, outputfilename )
    #   img.save( outputfilepath, format='PNG' )
    #
    #   ## keep track of all the processing we've finished
    #   #self.processedData[ str(f) ] = outputfilepath
    #   return (str(f), outputfilepath)

    def reset(self):
        '''
        new files should default to not showing dicom unless it has already been processed
        '''
        # hide frame navigation widgets
        # self.grid_remove()

        self.isLoaded = False
        self.dicom = None
        self.zframe.shown = False
        pngs_missing = False

        # detect if processed pngs listed in metadata file actually exist on system
        if self.app.Data.getFileLevel( 'processed' ) != None:
            if not os.path.exists(self.app.Data.unrelativize(self.app.Data.getFileLevel( 'processed' )['1'])):
                pngs_missing = True
        # update buttons
        if self.app.Data.getFileLevel( '.dicom' ) == None:
            self.loadBtn[ 'state' ] = DISABLED
            self.grid_remove()
            self.frame.grid()
            self.loadBtn.grid()
        else:
            self.loadBtn[ 'state' ] = NORMAL
            # and check if data is already processed
            if self.app.Data.getFileLevel( 'processed' ) != None and pngs_missing==False:
                self.load()
                self.zoomReset()
            else:
                self.grid_remove()
                self.frame.grid()
                self.loadBtn.grid()
                self.zframe.canvas.delete(ALL)

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
