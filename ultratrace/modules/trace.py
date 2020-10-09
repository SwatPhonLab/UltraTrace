from .base import Module
from .. import util
from ..util.logging import *
from ..widgets import Crosshairs, Header

import PIL
import random

from tkinter.ttk import Button, Entry, Frame, Scrollbar
from tkinter import Listbox, StringVar

class Trace(Module):
    '''
    Module to manage all of the different traces (with unique names/colors) and the
    Crosshairs objects associated to each one.  In particular, handles creation/modfication
    of traces and crosshairs.
    '''
    def __init__(self, app):
        info( ' - initializing module: Trace' )

        self.app = app

        self.displayedColour = None
        #self.app.Data.getCurrentTraceColor()

        # array of trace names for this directory
        self.available = self.app.Data.getTopLevel( 'traces' )
        self.available = {} if self.available==None else self.available

        # dictionary to hold trace -> [crosshairs] data
        self.crosshairs = {}

        # set of currently selected crosshairs
        self.selected = set()

        # set of copied crosshairs
        self.copied = []

        # declare & init trace string variable
        self.traceSV = StringVar()
        self.traceSV.set( '' )

        # frame for (most of) our widgets
        self.frame = Frame(self.app.LEFT)#, pady=7, padx=7)
        self.frame.grid( row=4 )

        # listbox to contain all of our traces
        lbframe = Frame(self.frame)
        self.scrollbar = Scrollbar(lbframe)
        self.listbox = Listbox(lbframe, yscrollcommand=self.scrollbar.set, width=12, height=5, exportselection=False, takefocus=0)
        self.scrollbar.config(command=self.listbox.yview)
        for trace in self.available:
            self.listbox.insert('end', trace)
        for i, item in enumerate(self.listbox.get(0, 'end')):
            # select our "default trace"
            if item==self.app.Data.getTopLevel( 'defaultTraceName' ):
                self.listbox.selection_clear(0, 'end')
                self.listbox.select_set( i )
                break
        else:
            self.listbox.select_set(0)
            # select whatever is listed first
            # TODO: this assumes that the list of traces is non-empty

        # this module is responsible for so many widgets that we need a different
        # strategy for keeping track of everything that needs constistent grid() /
        # grid_remove() behavior
        self.TkWidgets = [
            self.getWidget( Header(self.frame, text="Landmarks"), row=5, column=0, columnspan=4 ),
            self.getWidget( lbframe, row=10, column=0, rowspan=50 ),
            self.getWidget( Button(self.frame, text='Set as default', command=self.setDefaultTraceName, takefocus=0), row=10, column=1, columnspan=3 ),
            self.getWidget( Entry( self.frame, width=8, textvariable=self.displayedColour), row=13, column=1, columnspan=2, sticky='e'),
            self.getWidget( Button(self.frame, text='⟳', command=self.recolor, takefocus=0, width="1.5", style="symbol.TButton"), row=13, column=3, sticky='w'),
            self.getWidget( Button(self.frame, text='Clear', command=self.clear, takefocus=0), row=15, column=1, columnspan=3 ),
            self.getWidget( Entry( self.frame, width=12, textvariable=self.traceSV), row=100, column=0, sticky='w,e' ),
            self.getWidget( Button(self.frame, text='+', command=self.newTrace, takefocus=0, width=1.5), row=100, column=1, sticky='w' ),
            self.getWidget( Button(self.frame, text='Rename', command=self.renameTrace, takefocus=0, width="7"), row=100, column=2, columnspan=2 ) ]

        # there's probably a better way to do this than indexing into self.TkWidgets
        self.TkWidgets[3]['widget'].bind('<Return>', lambda ev: self.TkWidgets[0]['widget'].focus())
        self.TkWidgets[3]['widget'].bind('<Escape>', lambda ev: self.TkWidgets[0]['widget'].focus())
        self.TkWidgets[6]['widget'].bind('<Return>', lambda ev: self.TkWidgets[0]['widget'].focus())
        self.TkWidgets[6]['widget'].bind('<Escape>', lambda ev: self.TkWidgets[0]['widget'].focus())

        if util.get_platform() == 'Linux':
            self.app.bind('<Control-r>', self.recolor )
            self.app.bind('<Control-c>', self.copy )
            self.app.bind('<Control-v>', self.paste )
        else:
            self.app.bind('<Command-r>', self.recolor )
            self.app.bind('<Command-c>', self.copy )
            self.app.bind('<Command-v>', self.paste )
        self.grid()

    def update(self):
        ''' on change frames '''
        # self.grid()
        #NOTE this is called during zoom and pan
            #this means the crosshairs are redrawn for every <Motion> call, which is a lot
            #we could probably just move them instead
        self.reset() # clear our crosshairs
        self.read()  # read from file
        #self.frame.update()
        #debug("TraceModule", self.frame.winfo_width())
    def reset(self):
        ''' on change files '''
        # undraw all the crosshairs
        for trace in self.crosshairs:
            for ch in self.crosshairs[ trace ]:
                ch.undraw()
        # and empty out our trackers
        self.crosshairs = {}
        self.selected = set()

    def add(self, x, y, _trace=None, transform=True):
        '''
        add a crosshair to the zoom frame canvas
        '''

        trace = self.getCurrentTraceName() if _trace==None else _trace
        color  = self.available[ trace ]['color']
        ch = Crosshairs( self.app.Dicom.zframe, x, y, color, transform )
        if trace not in self.crosshairs:
            self.crosshairs[ trace ] = []
        self.crosshairs[ trace ].append( ch )
        return ch
    def remove(self, ch, write=True):
        '''
        remove a crosshair from the zoom frame canvas ... doesn't actually remove it
        but instead just makes it "invisible"
        '''

        ch.undraw()
        if write:
            self.write()
        return ch
    def move(self):
        ''' called when window resizes to move to correct relative locations'''
        # trace = self.getCurrentTraceName()
        if self.crosshairs:
            for trace in self.crosshairs:
                for ch in self.crosshairs[ trace ]:
                    truex,truey = ch.getTrueCoords()
                    ch.x,ch.y = ch.transformTrueToCoords(truex, truey)
                    ch.dragTo((ch.x,ch.y))

    def read(self):
        '''
        read a list of crosshair coordinates from the metadata file
        '''
        frame = self.app.frame
        for trace in self.available:
            try:
                newCrosshairs = []
                for item in self.app.Data.getTraceCurrentFrame(trace):
                    ch = self.add( item['x'], item['y'], _trace=trace, transform=False )
                    if trace not in self.crosshairs:
                        self.crosshairs[ trace ] = []
                    self.crosshairs[ trace ].append( ch )
                    newCrosshairs.append( ch )
                self.app.Control.push({ 'type':'add', 'chs':newCrosshairs })
            except KeyError:
                pass
    def write(self):
        '''
        write out the coordinates of all of our crosshairs to the metadata file:
        '''

        trace = self.getCurrentTraceName()
        traces = []

        # prepare trace data in format for metadata array
        if trace in self.crosshairs:
            for ch in self.crosshairs[ trace ]:
                if ch.isVisible:
                    x,y = ch.getTrueCoords()
                    data = { 'x':x, 'y':y }
                    if data not in traces:
                        # add trace to temporary array for including in metadata array
                        traces.append(data)
        # add to metadata array and update file
        self.app.Data.setCurrentTraceCurrentFrame( traces )
        # update tier labels for number of annotated frames
        self.app.TextGrid.updateTierLabels()

    def getCurrentTraceName(self):
        '''
        return string of current trace name
        '''

        try:
            return self.listbox.get(self.listbox.curselection())
        except Exception as e: # tkinter.TclError?
            error('Can\'t select from empty listbox!', e)
    def setDefaultTraceName(self):
        '''
        wrapper for changing the default trace
        '''
        self.app.Data.setTopLevel( 'defaultTraceName', self.getCurrentTraceName() )

    def select(self, ch):
        ''' select a crosshairs '''
        ch.select()
        self.selected.add(ch)
    def selectAll(self):
        ''' select all crosshairs '''
        if self.getCurrentTraceName() in self.crosshairs:
            for ch in self.crosshairs[self.getCurrentTraceName()]:
                self.select(ch)

    def unselect(self, ch):
        ''' unselect a crosshairs '''
        ch.unselect()
        self.selected.remove(ch)
    def unselectAll(self):
        ''' unselect all crosshairs '''
        for ch in self.selected:
            ch.unselect()
        self.selected = set()

    def getNearClickAllTraces(self, click):
        '''
        takes a click object ( (x,y) tuple ) and returns a list of crosshairs
        within _CROSSHAIR_SELECT_RADIUS

        first searches for crosshairs matching the current trace iterates
        thru the other traces if it doesnt find anything

        if nothing is found for any trace, returns None
        '''
        # get nearby crosshairs from this trace
        nearby = self.getNearClickOneTrace(click, self.getCurrentTraceName())
        if nearby != None:
            return nearby

        # otherwise
        else:
            # ... check our other traces to see if they contain any nearby guys
            for trace in self.available:
                nearby = self.getNearClickOneTrace(click, trace)
                # if we got something
                if nearby != None:
                    # switch to that trace and exit the loop
                    for i, item in enumerate(self.listbox.get(0, 'end')):
                        if item==trace:
                            self.listbox.selection_clear(0, 'end')
                            self.listbox.select_set( i )
                    return nearby

        return None
    def getNearClickOneTrace(self, click, trace):
        '''
        takes a click object and a trace and returns a list of crosshairs within
        util.CROSSHAIR_SELECT_RADIUS of that click
        '''

        # see if we clicked near any existing crosshairs
        possibleSelections = {}
        if trace in self.crosshairs:
            for ch in self.crosshairs[ trace ]:
                d = ch.getDistance(click)
                if d < util.CROSSHAIR_SELECT_RADIUS:
                    if d in possibleSelections:
                        possibleSelections[d].append( ch )
                    else:
                        possibleSelections[d] = [ ch ]

        # if we did ...
        if possibleSelections != {}:
            # ... get the closest one ...
            dMin = sorted(possibleSelections.keys())[0]
            # ... in case of a tie, select a random one
            ch = random.choice( possibleSelections[dMin] )
            return ch

        return None

    def copy(self, event=None):
        ''' copies relative positions of selected crosshairs for pasting'''
        # debug('copy')
        self.copied = []
        if len(self.selected) > 0:
            for ch in self.selected:
                self.copied.append(ch.getTrueCoords())
    def paste(self, event=None):
        ''' pastes copied crosshairs and add them to undo/redo buffer '''
        if len(self.copied) > 0:
            newChs = []
            for xy in self.copied:
                ch = self.add(xy[0],xy[1], transform=False)
                newChs.append(ch)
            self.write()
            self.app.Control.push({ 'type':'add', 'chs':newChs })

    def recolor(self, event=None, trace=None, color=None):
        ''' change the color of a particular trace '''

        trace = self.getCurrentTraceName() if trace==None else trace

        # grab a new color and save our old color (for generating Control data)
        newColor = self.getRandomHexColor() if color==None else color
        oldColor = self.app.Data.getCurrentTraceColor()

        self.available[ trace ]['color'] = newColor
        self.app.Data.setTraceColor( trace, newColor )

        if trace in self.crosshairs:
            for ch in self.crosshairs[ trace ]:
                ch.recolor( newColor )

        if trace==None or color == None:
            self.app.Control.push({ 'type':'recolor', 'trace':self.getCurrentTraceName(), 'color':oldColor })
            self.redoQueue = []
            # FIXME: get this to update the widget
            self.app.Trace.displayedColour = newColor
            # FIXME: also get the widget to update the colour!

        return oldColor
    def clear(self):
        ''' remove all crosshairs for the current trace '''

        # now we remove all the traces and save
        deleted = []
        trace = self.getCurrentTraceName()
        if trace in self.crosshairs:
            for ch in self.crosshairs[ trace ]:
                if ch.isVisible:
                    deleted.append( ch )
                self.remove( ch, write=False )
            self.write()

        self.app.Control.push({ 'type':'delete', 'chs':deleted })
    def newTrace(self):
        ''' add a new trace to our listbox '''

        # max length 12 chars (so it displays nicely)
        name = self.traceSV.get()[:12]

        # don't want to add traces we already have or empty strings
        if name not in self.available and len(name) > 0:

            # choose a random color
            color = self.getRandomHexColor()

            # save the new trace name and color to metadata & update vars
            self.available[ name ] = { 'color':color, 'files':{} }
            self.app.Data.setTopLevel( 'traces', self.available )
            self.traceSV.set('')

            # update our listbox
            self.listbox.insert('end', name)
            self.listbox.selection_clear(0, 'end')
            self.listbox.select_set( len(self.available)-1 )
    def renameTrace(self, oldName=None, newName=None):
        ''' change a trace name from oldName -> newName '''

        fromUndo = (oldName!=None or newName!=None)
        oldName = self.getCurrentTraceName() if oldName==None else oldName
        newName = self.traceSV.get()[:12] if newName==None else newName

        # don't overwrite anything
        if newName not in self.available and len(newName) > 0:

            # get data from the old name and change the dictionary key in the metadata
            data = self.available.pop( oldName )
            self.available[ newName ] = data
            self.app.Data.setTopLevel( 'traces', self.available )
            if oldName==self.app.Data.getTopLevel( 'defaultTraceName' ):
                self.app.Data.setTopLevel( 'defaultTraceName', newName )
            self.traceSV.set('')

            # update our listbox
            index = self.listbox.curselection()
            self.listbox.delete(index)
            self.listbox.insert(index, newName)
            self.listbox.selection_clear(0, 'end')
            self.listbox.select_set(index)

            if not( fromUndo ):
                self.app.Control.push({ 'type':'rename', 'old':oldName, 'new':newName })

    def getRandomHexColor(self):
        ''' helper for getting a random color '''
        return '#%06x' % random.randint(0, 0xFFFFFF)
    def getWidget(self, widget, row=0, column=0, rowspan=1, columnspan=1, sticky=() ):
        ''' helper for managing all of our widgets '''
        return {
            'widget' : widget,
            'row'    : row,
            'rowspan': rowspan,
            'column' : column,
            'columnspan':columnspan,
            'sticky' : sticky }

    def grid(self):
        ''' grid all of our widgets '''
        for item in self.TkWidgets:
            item['widget'].grid(
                row=item['row'], column=item['column'], rowspan=item['rowspan'],
                columnspan=item['columnspan'], sticky=item['sticky'] )
        self.listbox.pack(side='left', fill='y')
        self.scrollbar.pack(side='right', fill='y')
    def grid_remove(self):
        ''' remove all of our widgets from the grid '''
        for item in self.TkWidgets:
            item['widget'].grid_remove()
        self.listbox.packforget()
        self.scrollbar.packforget()

