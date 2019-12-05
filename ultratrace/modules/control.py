from .base import Module
from .. import util
from ..util.logging import *

from tkinter import Button, Frame

class Control(Module):
    '''
    This class provides a clean interface for managing Undo/Redo functionality.
    Implementation relies on storing two lists of actions as stacks, one for Undo
    and one for Redo.  Calling Undo/Redo should pop the corresponding stack and
    execute the inverse of that action, pushing the inverse action to the other
    stack (so its inversion can also be executed).

    Note: both stacks get cleared on
        - change files
        - change frames
        - Dicom.resetZoom()
    '''
    def __init__(self, app):
        info( ' - initializing module: Control' )
        # reference to our main object containing other functionality managers
        self.app = app
        # initialize our stacks
        self.reset()
        # bind Ctrl+z to UNDO and Ctrl+Shift+Z to REDO
        if util.get_platform() == 'Linux':
            self.app.bind('<Control-z>', self.undo )
            self.app.bind('<Control-Z>', self.redo )
        else:
            self.app.bind('<Command-z>', self.undo )
            self.app.bind('<Command-Z>', self.redo )
        # also make some buttons and bind them
        self.frame = Frame(self.app.LEFT)#, pady=7)
        self.frame.grid( row=5 )
        self.undoBtn = Button(self.frame, text='Undo', command=self.undo, takefocus=0)
        self.redoBtn = Button(self.frame, text='Redo', command=self.redo, takefocus=0)
        self.updateButtons()
    def push(self, item):
        '''
        add an item to the undo-stack
        and empty out the redo-stack
        '''
        self.uStack.append( item )
        self.rStack = []
        self.updateButtons()
    def reset(self):
        ''' reset our stacks '''
        self.uStack = [] # undo
        self.rStack = [] # redo
    def update(self):
        ''' changing files and changing frames should have the same effect '''
        self.reset()
    def undo(self, event=None):
        ''' perform the undo-ing '''

        if len(self.uStack):
            item = self.uStack.pop()

            if item['type'] == 'add':
                chs = item['chs']
                for ch in chs:
                    self.app.Trace.remove( ch )
                self.rStack.append({ 'type':'delete', 'chs':chs })
            elif item['type'] == 'delete':
                chs = item['chs']
                for ch in chs:
                    ch.draw()
                self.rStack.append({ 'type':'add', 'chs':chs })
            elif item['type'] == 'move':
                chs = item['chs']
                coords = item['coords']
                for i in range(len(chs)):
                    chs[i].dragTo( coords[i] )
                self.rStack.append({ 'type':'move', 'chs':chs, 'coords':coords })
            elif item['type'] == 'recolor':
                oldColor = self.app.Trace.recolor( item['trace'], item['color'] )
                self.rStack.append({ 'type':'recolor', 'trace':item['trace'], 'color':oldColor })
            elif item['type'] == 'rename':
                self.app.Trace.renameTrace( newName=item['old'], oldName=item['new'] ) # this is backwards on purpose
                self.rStack.append({ 'type':'rename', 'old':item['old'], 'new':item['new'] })
            else:
                error(item)
                raise NotImplementedError

            self.app.Trace.unselectAll()
            self.app.Trace.write()
            self.updateButtons()
        else:
            warn( 'Nothing to undo!' )
    def redo(self, event=None):
        ''' perform the redo-ing '''

        if len(self.rStack):
            item = self.rStack.pop()

            if item['type'] == 'add':
                chs = item['chs']
                for ch in chs:
                    self.app.Trace.remove( ch )
                self.uStack.append({ 'type':'delete', 'chs':chs })
            elif item['type'] == 'delete':
                chs = item['chs']
                for ch in chs:
                    ch.draw()
                self.uStack.append({ 'type':'add', 'chs':chs })
            elif item['type'] == 'move':
                chs = item['chs']
                coords = item['coords']
                for i in range(len(chs)):
                    chs[i].dragTo( coords[i] )
                self.uStack.append({ 'type':'move', 'chs':chs, 'coords':coords })
            elif item['type'] == 'recolor':
                oldColor = self.app.Trace.recolor( item['trace'], item['color'] )
                self.uStack.append({ 'type':'recolor', 'trace':item['trace'], 'color':oldColor })
            elif item['type'] == 'rename':
                self.app.Trace.renameTrace( newName=item['new'], oldName=item['old'] )
                self.uStack.append({ 'type':'rename', 'old':item['old'], 'new':item['new'] })
            else:
                error(item)
                raise NotImplementedError

            self.app.Trace.unselectAll()
            self.app.Trace.write()
            self.updateButtons()
        else:
            warn( 'Nothing to redo!' )
    def updateButtons(self):
        '''
        Don't allow clicking buttons that wrap empty stacks.  However, users will
        still be able to access that functionality thru key bindings.
        '''
        self.undoBtn['state'] = NORMAL if len(self.uStack) else DISABLED
        self.redoBtn['state'] = NORMAL if len(self.rStack) else DISABLED
        self.grid()
    def grid(self):
        '''
        Grid button widgets
        '''
        self.undoBtn.grid(row=0, column=0)
        self.redoBtn.grid(row=0, column=1)
    def grid_remove(self):
        '''
        Remove button widgets from grid
        '''
        self.undoBtn.grid_remove()
        self.redoBtn.grid_remove()
