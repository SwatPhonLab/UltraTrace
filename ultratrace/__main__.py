#!/usr/bin/env python3

from .modules import *
from . import util
from .util.logging import *
from .widgets import *

# core libs
from tkinter import *
from tkinter.ttk import *
from tkinter import filedialog
# import soundfile as sf
# import numpy as np
# import scipy.fftpack as fftpack
# import urllib.request as request
import argparse, datetime, json, \
	math, os, sys, random, shutil, warnings, decimal, re,\
	soundfile as sf, scipy.fftpack as fftpack, urllib.request as request #FIXME should I put these with non-critical dependencies?

import parselmouth
import copy

import base64

# monkeypatch the warnings module
warnings.showwarning = lambda msg, *args : warn(msg)

# critical dependencies
from magic import Magic # sudo -H pip3 install -U python-magic
getMIMEType = Magic(mime=True).from_file
import PIL

# non-critical dependencies
try:
	# import pygame 	# sudo -H pip3 install pygame pygame.mixer && brew install sdl sdl_mixer
	# assert("pygame.mixer" in sys.modules)
	from pydub import AudioSegment
	# from pydub.playback import play
	import pyaudio
	# import wave
	# import simpleaudio as sa
	_AUDIO_LIBS_INSTALLED = True
except (ImportError, AssertionError):
	warnings.warn('Audio library failed to load')
	_AUDIO_LIBS_INSTALLED = False
try:
	import cairosvg # sudo -H pip3 install cairosvg && brew install cairo
	import wav2vec  # sudo -H pip3 install wav2vec
	_WAV_VIS_LIBS_INSTALLED = True
except (ImportError):
	warnings.warn('Waveform visualization library failed to load')
	_WAV_VIS_LIBS_INSTALLED = False
try:
    debug('Loading platform-specific enhancements for ' + util.get_platform())
    if util.get_platform() == 'Linux':
        import xrp  # pip3 install xparser
        from ttkthemes import ThemedTk
        from pathlib import Path
    else:
        from ttkthemes import ThemedTk
except (ImportError):
    warnings.warn('Can\'t load platform-specific enhancements')
    ThemedTk = Tk


class ControlModule(object):
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

class SearchModule:
	def __init__(self, app):
		self.app = app
		self.window = None

		self.context_size = 3
		self.results = []
		self.regex = StringVar(self.app)

		# if anything ever changes the contents of any intervals
		# it should call SearchModule.loadIntervals()
		self.intervals = []
		self.loadIntervals()
	def handleClose(self, event=None):
		self.window.destroy()
		self.window = None
	def createWindow(self):
		self.window = Toplevel(self.app)
		self.window.title('Search')
		self.window.protocol("WM_DELETE_WINDOW", self.handleClose)
		self.input = Entry(self.window, textvariable=self.regex)
		self.input.grid(row=0, column=0)
		self.input.bind('<Return>', self.search)
		self.input.bind('<Escape>', lambda ev: self.window.focus())
		self.searchButton = Button(self.window, text='Search', command=self.search, takefocus=0)
		self.searchButton.grid(row=0, column=1)
		self.resultCount = Label(self.window, text='0 results')
		self.resultCount.grid(row=0, column=2)
		cols = ('File', 'Tier', 'Time', 'Text')
		self.scroll = Scrollbar(self.window, orient='vertical')
		self.resultList = Treeview(self.window, columns=cols, show="headings", yscrollcommand=self.scroll.set, selectmode='browse')
		self.scroll.config(command=self.resultList.yview)
		for col in cols:
			self.resultList.heading(col, text=col)
		self.resultList.grid(row=2, column=0, columnspan=3, sticky=N+S+E+W)
		self.resultList.bind('<Double-1>', self.onClick)
		Grid.rowconfigure(self.window, 2, weight=1)
		Grid.columnconfigure(self.window, 0, weight=1)
		self.scroll.grid(row=2, column=3, sticky=N+S)
	def openSearch(self):
		if self.window == None:
			self.createWindow()
		self.window.lift()
		self.input.focus()
	def loadIntervals(self):
		filecount = len(self.app.Data.getTopLevel('files'))
		self.intervals = []
		for f in range(filecount):
			filename = self.app.Data.getFileLevel('name', f)
			tg = self.app.Data.getFileLevel('.TextGrid', f)
			if tg:
				grid = self.app.TextGrid.fromFile(self.app.Data.unrelativize(tg))
				for tier in grid:
					if TextGridModule.isIntervalTier(tier):
						for el in tier:
							if el.mark:
								self.intervals.append((el, tier.name, filename))
	def search(self, event=None):
		if self.regex.get() == '':
			self.results = []
		else:
			pat = re.compile(self.regex.get(), re.IGNORECASE | re.MULTILINE | re.DOTALL)
			self.results = []
			for i in self.intervals:
				s = pat.search(i[0].mark)
				if s:
					disp = i[0].mark
					a = max(0, s.start()-self.context_size)
					b = min(s.end()+self.context_size, len(disp))
					self.results.append(i + (('...' if a > 0 else '')+disp[a:b]+('...' if b < len(disp) else ''),))
		self.resultCount.configure(text='%s results' % len(self.results))
		for kid in self.resultList.get_children():
			self.resultList.delete(kid)
		for row, res in enumerate(self.results):
			ls = (res[2], res[1], '%s-%s' % (res[0].minTime, res[0].maxTime), res[3])
			self.resultList.insert('', 'end', iid=str(row), values=ls)
	def onClick(self, event=None):
		self.jumpTo(int(self.resultList.selection()[0]))
	def jumpTo(self, index):
		self.app.filesJumpTo(self.results[index][2])
		self.app.TextGrid.selectedTier.set(self.results[index][1])
		self.app.TextGrid.start = self.results[index][0].minTime
		self.app.TextGrid.end = self.results[index][0].maxTime
		for i, f in enumerate(self.app.TextGrid.frameTier):
			if f.time >= self.results[index][0].minTime:
				self.app.frameSV.set(str(i))
				self.app.framesJumpTo()
				break
		self.app.TextGrid.fillCanvases()

class App(ThemedTk):
	'''
	This class is neatly wraps all the functionality of our application.  By itself,
	it's is responsible for handling command line input, navigating between files,
	navigating between frames, handling of some events, and coordinating other core
	functionality (which is handled by individual `modules`).

	Note:
		- when we change files, modules should execute MODULE.reset() methods
		- when we change frames, modules should execute MODULE.update() methods
		- modules that are responsible for managing their own widgets should have
			MODULE.grid() and MODULE.grid_remove() methods to wrap corresponding
			functionality for their widgets
	'''
	def __init__(self):

		info( 'initializing UltraTrace' )

		# do the normal Tk init stuff
		if util.get_platform()=='Linux':
			try:
				Xresources = xrp.parse_file(os.path.join(str(Path.home()), '.Xresources'))
				if '*TtkTheme' in Xresources.resources:
					ttktheme = Xresources.resources['*TtkTheme']
					info("Setting Linux Ttk theme to {}".format(ttktheme))
				elif '*TkTheme' in Xresources.resources:
					ttktheme = Xresources.resources['*TkTheme']
					info("Setting Linux Tk theme to {}".format(ttktheme))
				else:
					ttktheme = "clam"  # alt, clam, classic, default
					info("Falling back to default Linux Tk theme: {}".format(ttktheme))
				super().__init__(theme=ttktheme)
			except Exception as e:
				error("exception: ", e)
				super().__init__()
		else:
			super().__init__()
		self.title('UltraTrace')

		# check if we were passed a command line argument
		parser = argparse.ArgumentParser(prog='UltraTrace')
		parser.add_argument('path', help='path (unique to a participant) where subdirectories contain raw data', default=None, nargs='?')
		args = parser.parse_args()

		# initialize data module
		self.Data = MetadataModule( self, args.path )

		# initialize the main app widgets
		self.setWidgetDefaults()
		self.buildWidgetSkeleton()

		# initialize other modules
		self.Control = ControlModule(self)
		self.Trace = TraceModule(self)
		self.Dicom = DicomModule(self)
		self.Audio = PlaybackModule(self)
		self.TextGrid = TextGridModule(self)
		self.Spectrogram = SpectrogramModule(self)
		self.Search = SearchModule(self)

		info( ' - loading widgets' )

		self.filesUpdate()
		# self.framesUpdate()
		# self.TextGrid.startup() #NOTE why does TextGridModule have to reset a second time? Is there a more economical way to do this?


		# to deal with resize handler being called multiple times
		# in a single window resize
		self.isResizing = False

		self.oldwidth = self.winfo_width()

		self.after(300,self.afterstartup)

	def setWidgetDefaults(self):
		'''
		Need to set up some defaults here before building Tk widgets (this is specifically
		true w/r/t the StringVars)
		'''
		self.currentFID = 0 	# file index w/in list of sorted files
		self.frame = 0			# current frame of dicom file
		self.isClicked = False	# used in handling of canvas click events
		self.isDragging = False # used in handling of canvas click events
		# self.resized = False 	#for changing widgets after window resize
		self.selectBoxX = False
		self.selectBoxY = False

		# declare string variables
		self.currentFileSV = StringVar(self)
		self.frameSV = StringVar(self)

		# initialize string variables
		self.currentFileSV.set( self.Data.files[ self.currentFID ] )
		self.frameSV.set( '1' )
	def buildWidgetSkeleton(self):
		'''
		Builds the basic skeleton of our app widgets.
			- items marked with (*) are built directly in this function
			- items marked with (~) are built by the individual modules
			# WARNING: out of date diagram
		.________________________________________.
		|	ROOT 						         |
		| .____________________________________. |
		| |          TOP*                      | |
		| | ._______________. .______________. | |
		| | |   LEFT*       | |   RIGHT*     | | |
		| | |   - file nav* | |   - dicom~   | | |
		| | |   - frame nav*| |              | | |
		| | |   - traces~   | |              | | |
		| | |   - undo~     | |              | | |
		| | \_______________/ \______________/ | |
		| \____________________________________/ |
		|	    							     |
		| .____________________________________. |
		| |           BOTTOM*                  | |
		| |           - spectrogram~           | |
		| |           - textgrid~              | |
		| \____________________________________/ |
		\________________________________________/
		'''
		# main Frame skeleton
		self.TOP = Frame(self)
		self.TOP.columnconfigure(1,weight=1, minsize=320)
		self.TOP.rowconfigure(0,weight=1, minsize=240)
		self.LEFT = Frame(self.TOP)
		# self.LEFT.rowconfigure(0,weight=1)
		# self.LEFT.columnconfigure(0,weight=1)
		self.RIGHT = Frame(self.TOP)
		self.RIGHT.rowconfigure(0,weight=1)
		self.RIGHT.columnconfigure(0,weight=1)
		self.BOTTOM = Frame(self)
		# self.BOTTOM.columnconfigure(0,weight=1)
		self.BOTTOM.columnconfigure(1,weight=1)
		# self.BOTTOM.rowconfigure(0,weight=1)
		# self.TOP.grid(    row=0, column=0, sticky=NW)
		# self.LEFT.grid(   row=0, sticky=N )
		# self.RIGHT.grid(  row=0, column=1)
		# self.BOTTOM.grid( row=1, column=0, sticky=E)
		self.TOP.grid(    row=0, column=0, sticky=N+E+S+W)
		self.LEFT.grid(   row=0, sticky=N+E+S+W )
		self.RIGHT.grid(  row=0, column=1, sticky=N+E+S+W)
		self.BOTTOM.grid( row=1, column=0, sticky=N+E+S+W)
		self.pady=3
		self.columnconfigure(0,weight=1)
		self.rowconfigure(0,weight=1)

		# navigate between all available filenames in this directory
		self.filesFrame = Frame(self.LEFT)#, pady=7)
		self.filesPrevBtn = Button(self.filesFrame, text='<', command=self.filesPrev, takefocus=0)
		self.filesJumpToMenu = OptionMenu(self.filesFrame, self.currentFileSV, *self.Data.files, command=self.filesJumpTo)
		self.filesNextBtn= Button(self.filesFrame, text='>', command=self.filesNext, takefocus=0)
		self.filesFrame.grid( row=1 )
		self.filesPrevBtn.grid( row=1, column=0 )
		self.filesJumpToMenu.grid( row=1, column=1 )
		self.filesNextBtn.grid(row=1, column=2 )
		Header(self.filesFrame, text="Choose a file:").grid( row=0, column=0, columnspan=3 )

		# navigate between frames
		self.framesFrame = Frame(self.LEFT)#, pady=7)
		self.framesSubframe = Frame(self.framesFrame)
		self.framesPrevBtn = Button(self.framesSubframe, text='<', command=self.framesPrev, takefocus=0)
		self.framesEntryText = Entry(self.framesSubframe, width=5, textvariable=self.frameSV)
		self.framesEntryBtn = Button(self.framesSubframe, text='Go', command=self.framesJumpTo, takefocus=0)
		self.framesNextBtn= Button(self.framesSubframe, text='>', command=self.framesNext, takefocus=0)
		self.framesHeader = Header(self.framesFrame, text="Choose a frame:")
		self.framesFrame.grid( row=3 )
		self.framesSubframe.grid( row=1 )

		# non-module-specific bindings
		self.bind('<Option-Left>', self.filesPrev )
		self.bind('<Option-Right>', self.filesNext )
		self.bind('<Left>', self.framesPrev )
		self.bind('<Right>', self.framesNext )
		self.bind('<BackSpace>', self.onBackspace )
		self.bind('<Button-1>', self.getWinSize)
		self.bind('<ButtonRelease-1>', self.onRelease)
		self.bind('<Double-Button-1>', self.onDoubleClick)
		self.bind('<Escape>', self.onEscape )
		# self.count = 0

		self.framesEntryText.bind('<Return>', self.unfocusAndJump)
		self.framesEntryText.bind('<Escape>', lambda ev: self.framesFrame.focus())

		# force window to front
		self.lift()

	def lift(self):
		'''
		Bring window to front (doesn't shift focus to window)
		'''
		self.attributes('-topmost', 1)
		self.attributes('-topmost', 0)
	def afterstartup(self):
		'''

		'''
		self.bind('<Configure>', self.alignBottomLeftWrapper )
		self.alignBottomLeft()
		self.getWinSize()
		self.alignBottomRight(self.oldwidth-self.leftwidth)
		if self.Dicom.zframe.image:
			self.Dicom.zframe.setImage(self.Dicom.zframe.image)

	def alignBottomLeftWrapper(self, event=None):
		if self.isResizing: return
		self.isResizing = True
		self.after(100, lambda: self.alignBottomLeft(event))

	def alignBottomLeft(self, event=None):
		'''
		Makes the length of the canvases on the lower left the same length as the pane of controls in self.LEFT
		'''
		self.leftwidth = self.LEFT.winfo_width()
		for t in range(len(self.TextGrid.TkWidgets)):
			tierWidgets = self.TextGrid.TkWidgets[t]
			if 'frames' in tierWidgets:
				tierWidgets['frames-label'].config(width=self.leftwidth)
				tierWidgets['frames-label'].coords(ALL,(self.leftwidth,tierWidgets['frames-label'].coords(1)[1]))
			if 'canvas' in tierWidgets:
				tierWidgets['canvas-label'].config(width=self.leftwidth)
				tierWidgets['canvas-label'].coords(ALL,(self.leftwidth,tierWidgets['canvas-label'].coords(1)[1]))
		if event == None or event.widget == self:
			self.alignBottomRight(self.winfo_width() - self.leftwidth)
			self.Dicom.zframe.setImage(self.Dicom.zframe.image)
		self.isResizing = False
	def alignBottomRight(self,x):
		''' '''
		self.Spectrogram.canvas_width = x
		self.Spectrogram.canvas.config(width=x)
		self.TextGrid.canvas_width = x
		for t in range(len(self.TextGrid.TkWidgets)):
			tierWidgets = self.TextGrid.TkWidgets[t]
			canvas = None
			if 'frames' in tierWidgets:
				tierWidgets['frames'].config(width=x)
			elif 'canvas' in tierWidgets:
				tierWidgets['canvas'].config(width=x)
			if 'times' in tierWidgets:
				tierWidgets['times'].config(width=x)
				tierWidgets['times'].coords(2,(x,tierWidgets['times'].coords(2)[1])) #move end time
				tierWidgets['times'].coords(3,(x/2,tierWidgets['times'].coords(3)[1]))
		self.TextGrid.fillCanvases() #calls Spectrogram.reset

	# def onWindowResize(self, event):
	# 	'''
	# 	Handle moving or resizing the app window
	# 	'''
	# 	self.alignBottomLeft()
	# 	# self.resized=True

	def getWinSize(self, event=None):
		self.oldwidth = self.winfo_width()
	def onDoubleClick(self, event):
		''' select only crosshairs that's double clicked'''
		nearby = self.Trace.getNearClickAllTraces( (event.x, event.y) )
		if nearby != None:
			self.Trace.unselectAll()
			self.Trace.select( nearby )
	def onClickZoom(self, event):
		'''
		Handle clicking within the zoomframe canvas
		'''
		if self.Dicom.isLoaded:
			self.click = (event.x, event.y)
			self.isDragging = False

			# get nearby crosshairs from this trace
			nearby = self.Trace.getNearClickAllTraces( self.click )

			# if we didn't click near anything ...
			if nearby == None:
				self.Trace.unselectAll()
				if event.state != 1:
					# unselect crosshairs
					self.isClicked = True
					ch = self.Trace.add( *self.click )
					self.Control.push({ 'type':'add', 'chs':[ch] })
				else:
					self.selectBoxX = self.Dicom.zframe.canvas.canvasx(event.x)
					self.selectBoxY = self.Dicom.zframe.canvas.canvasy(event.y)
				return

			# NOTE: only get here if we clicked near something

			# if holding option key, unselect the guy we clicked on
			# if event.state == 16:
			# if holding shift key, and ch is selected, unselect it
			if event.state == 1 and nearby in self.Trace.selected:
				nearby.unselect()
				if nearby in self.Trace.selected:
					self.Trace.selected.remove( nearby )

			# otherwise, if not selected, add it to our selection
			elif nearby not in self.Trace.selected:
				if event.state != 1: #and nearby.isSelected == False:
					self.Trace.unselectAll()

				# add this guy to our current selection
				self.Trace.select( nearby )
			#through all of these operations, if clicked ch is selected, is ready to be dragged
			if nearby in self.Trace.selected:
				# set dragging variables
				self.isDragging = True
				self.dragClick = self.click

	def onReleaseZoom(self, event):
		'''
		Handle releasing a click within the zoomframe canvas
		'''
		if self.Dicom.isLoaded:

			# select multiple crosshairs
			if self.selectBoxX!=False:
				canvas = self.Dicom.zframe.canvas
				x1=self.selectBoxX
				x2=canvas.canvasx(event.x)
				y1=self.selectBoxY
				y2=canvas.canvasy(event.y)
				self.selectBoxX = False
				self.selectBoxY = False

				trace = self.Trace.getCurrentTraceName()
				coords = []
				x1True = None

				if trace in self.Trace.crosshairs:
					for ch in self.Trace.crosshairs[ trace ]:
						if x1True == None:
							x1True, y1True = ch.transformCoordsToTrue(x1,y1)
							x2True, y2True = ch.transformCoordsToTrue(x2,y2)
						if ch.isVisible:
							x,y = ch.getTrueCoords()
							if min(x1True,x2True) < x < max(x1True,x2True) and min(y1True,y2True) < y < max(y1True,y2True):
								self.Trace.select(ch)

			self.isDragging = False
			self.isClicked = False
			self.Trace.write()
	def onReleaseSpec(self,event):
		'''shift + release zooms textgrid & spectrogram to selected interval'''
		if self.Spectrogram.specClick==True:
			# if event.state==257:
			canvas = self.Spectrogram.canvas
			t1 = self.Spectrogram.clicktime
			t2 = self.Spectrogram.xToTime(canvas.canvasx(event.x))
			# self.TextGrid.start = decimal.Decimal(min(t1,t2))
			# self.TextGrid.end = decimal.Decimal(max(t1,t2))
			# for itm in canvas.find_all()[0]:
				# for tag in canvas.gettags(itm): #canvas.dtag() does not seem to work with one argument
			if max(t1,t2) - min(t1,t2) > self.Spectrogram.ts: #if selected area is larger than one strip of Spectrogram
				#gets rid of previous tags
				for tag in canvas.gettags(canvas.find_all()[0]):
					canvas.dtag(canvas.find_all()[0],tag)
				a = self.Spectrogram.timeToX(self.Spectrogram.clicktime)
				b = event.x
				x1 = min(a,b)
				x2 = max(a,b)
				#find all frames within range, and add them as tags
				frame_i = self.TextGrid.frames_canvas.find_all()[0]
				current_loc = self.TextGrid.frames_canvas.coords(frame_i)[0]
				while current_loc < x2:
					if current_loc > x1:
						tag = self.TextGrid.frames_canvas.gettags(frame_i)[0]
						canvas.addtag_all(tag)
					frame_i += 1
					current_loc = self.TextGrid.frames_canvas.coords(frame_i)[0]
				canvas.addtag_all('minTime'+str(self.Spectrogram.xToTime(x1)))
				canvas.addtag_all('maxTime'+str(self.Spectrogram.xToTime(x2)))
				self.TextGrid.selectedItem = (canvas, canvas.find_all()[0])
				self.TextGrid.setSelectedIntvlFrames(self.TextGrid.selectedItem)
				# self.TextGrid.paintCanvases()
				# self.Spectrogram.drawInterval(l_loc=x1,r_loc=x2)
				# debug(canvas.gettags(ALL))
				# specgram = self.Spectrogram.canvas.find_all()[0]
				# self.TextGrid.fillCanvases()
				self.TextGrid.genFrameList(widg=canvas,x_loc=x2, SI=True)
			self.Spectrogram.specClick = False
			self.Spectrogram.clicktime = -1

	def onRelease(self,event):
		'''

		'''
		#runs if click happened on specific canvases
		self.onReleaseZoom(event)
		self.onReleaseSpec(event)
		#runs if window resized
		# if self.resized == True and self.Dicom.zframe.shown == True: #shouldn't trigger when frame not displayed
		if self.winfo_width() != self.oldwidth and self.Dicom.zframe.shown == True: #shouldn't trigger when frame not displayed
			# self.resized = False
			#resize dicom image
			png_loc = self.Data.getPreprocessedDicom(self.frame)
			image = PIL.Image.open( png_loc )
			self.Dicom.zframe.setImage(image)
			# x = self.Dicom.zframe.width
			x = self.winfo_width() - self.LEFT.winfo_width()
			# y = self.Dicom.zframe.height
			#resize TextGrid tiers and spectrogram
			self.alignBottomRight(x)
			#move Traces
			self.Trace.move()

			#save layout ot geometry manager
			geometry = self.geometry()
			self.Data.setTopLevel( 'geometry', geometry )

	def onMotion(self, event):
		'''
		Handle mouse movement within the zoomframe canvas
		'''
		if self.Dicom.isLoaded:

			if self.isDragging: # dragging selection
				thisClick = (event.x, event.y)
				selected = list(self.Trace.selected)
				coords = []
				# move all currently selected crosshairs
				for sch in selected:
					# keep their relative distance constant
					center = ( sch.x, sch.y ) # canvas coordinates not true coordinates
					newX = event.x + center[0] - self.dragClick[0]
					newY = event.y + center[1] - self.dragClick[1]
					sch.dragTo( (newX,newY) )
					coords.append( center )

				self.dragClick = thisClick
				self.Control.push({ 'type':'move', 'chs':selected, 'coords':coords })

			elif self.isClicked: # no selection, mouse clicked
				lastClick = self.click
				thisClick = (event.x, event.y)
				# enforce minimum distance b/w new crosshairs
				dx = abs(thisClick[0] - lastClick[0]) / self.Dicom.zframe.imgscale
				dy = abs(thisClick[1] - lastClick[1]) / self.Dicom.zframe.imgscale
				if dx > util.CROSSHAIR_DRAG_BUFFER or dy > util.CROSSHAIR_DRAG_BUFFER:
					self.click = thisClick
					ch = self.Trace.add( *self.click )
					self.Control.push({ 'type':'add', 'chs':[ch] })
	def onEscape(self, event):
		'''
		Handle <Esc> key : empties the current selection
		'''
		self.isDragging = False
		self.isClicked = False
		self.Trace.unselectAll()
	def onBackspace(self, event):
		'''
		Handle <Backspace> key : removes current selection
		'''
		for sch in self.Trace.selected:
			self.Trace.remove( sch )
		self.Control.push({ 'type':'delete', 'chs':self.Trace.selected })
		self.Trace.unselectAll()

	def filesUpdate(self):
		'''
		Changes to be executed every time we change files
		'''
		# update variables
		self.currentFileSV.set( self.Data.files[ self.currentFID ] )
		self.frame = 1
		self.frames= 1

		# reset modules
		self.Control.reset()
		self.Trace.reset()
		self.Dicom.reset() # need this after Trace.reset() #NOTE is this still true?
		self.Audio.reset()
		self.TextGrid.reset()
		self.Spectrogram.reset()

		# check if we can pan left/right
		self.filesPrevBtn['state'] = DISABLED if self.Data.getFileLevel('_prev')==None else NORMAL
		self.filesNextBtn['state'] = DISABLED if self.Data.getFileLevel('_next')==None else NORMAL
		#load first frame
		self.framesUpdate()

	def filesPrev(self, event=None):
		'''
		controls self.filesPrevBtn for panning between available files
		'''
		if self.Data.getFileLevel( '_prev' ) != None:
			# change the index of the current file
			self.currentFID -= 1
			# update
			self.filesUpdate()
	def filesNext(self, event=None):
		'''
		controls self.filesNextBtn for panning between available files
		'''
		if self.Data.getFileLevel( '_next' ) != None:
			# change the index of the current file
			self.currentFID += 1
			# update
			self.filesUpdate()
	def filesJumpTo(self, choice):
		'''
		jump directly to an available file (from the OptionMenu widget)
		'''
		self.currentFID = self.Data.files.index( choice )
		self.filesUpdate()

	def framesUpdate(self):
		'''
		Changes to be executed every time we change frames
		'''
		# frameTier = self.TextGrid.TextGrid.getFirst(self.TextGrid.frameTierName)
		# if

		# update variables
		self.frameSV.set( str(self.frame) )

		# update modules
		self.Control.update()
		self.Dicom.update()
		self.Trace.update()
		self.Audio.update()
		self.TextGrid.update()
		self.Spectrogram.update()

		# check if we can pan left/right
		self.framesPrevBtn['state'] = DISABLED if self.frame==self.TextGrid.startFrame else NORMAL
		self.framesNextBtn['state'] = DISABLED if self.frame==self.TextGrid.endFrame else NORMAL

	def framesPrev(self, event=None):
		'''
		controls self.framesPrevBtn for panning between frames
		'''
		# if self.Dicom.isLoaded and self.frame > self.TextGrid.startFrame:
		if isinstance(self.focus_get(), (Entry, Spinbox)): return
		if self.frame > self.TextGrid.startFrame:
			self.frame -= 1
			# if len(self.TextGrid.selectedIntvlFrames) != 0:
			# 	while str(self.frame) not in self.TextGrid.selectedIntvlFrames or self.frame > self.TextGrid.last_frame:
			# 		if self.frame <= int(self.TextGrid.selectedIntvlFrames[0]):
			# 			self.frame = int(self.TextGrid.selectedIntvlFrames[0])
			# 			break
			# 		self.frame -= 1
			self.framesUpdate()
	def framesNext(self, event=None):
		'''
		controls self.framesNextBtn for panning between frames
		'''
		# if self.Dicom.isLoaded and self.frame < self.TextGrid.endFrame:
		if isinstance(self.focus_get(), (Entry, Spinbox)): return
		if self.frame < self.TextGrid.endFrame:
			self.frame += 1
			# if len(self.TextGrid.selectedIntvlFrames) != 0:
			# 	while str(self.frame) not in self.TextGrid.selectedIntvlFrames or self.frame < self.TextGrid.first_frame:
			# 		if self.frame >= int(self.TextGrid.selectedIntvlFrames[-1]):
			# 			self.frame = int(self.TextGrid.selectedIntvlFrames[-1])
			# 			break
			# 		self.frame += 1
			self.framesUpdate()
	def unfocusAndJump(self, event):
		self.framesJumpTo()
		self.framesFrame.focus()
	def framesJumpTo(self):
		'''
		jump directly to a frame (from the Entry widget)
		'''
		try:

			choice = int( self.frameSV.get() )

			if choice<1:
				self.frame = 1
			elif choice>self.frames:
				self.frame = self.frames
			else:
				self.frame = choice

			self.framesUpdate()

		except ValueError:
			error( 'Please enter an integer!' )

def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 25, fill = '█'):
	"""
	Call in a loop to create terminal progress bar
	@params:
		iteration   - Required  : current iteration (Int)
		total       - Required  : total iterations (Int)
		prefix      - Optional  : prefix string (Str)
		suffix      - Optional  : suffix string (Str)
		decimals    - Optional  : positive number of decimals in percent complete (Int)
		length      - Optional  : character length of bar (Int)
		fill        - Optional  : bar fill character (Str)
	"""
	percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
	filledLength = int(length * iteration // total)
	bar = fill * filledLength + '-' * (length - filledLength)
	print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = '\r')
	# Print New Line on Complete
	if iteration == total:
		print()

class CanvasTooltip:
    '''
    It creates a tooltip for a given canvas tag or id as the mouse is
    above it.

    This class has been derived from the original Tooltip class I updated
    and posted back to StackOverflow at the following link:

    https://stackoverflow.com/questions/3221956/
           what-is-the-simplest-way-to-make-tooltips-in-tkinter/
           41079350#41079350

    Alberto Vassena on 2016.12.10.
    '''

    def __init__(self, canvas, tag_or_id,
                 *,
                 bg='#FFFFEA',
                 pad=(5, 3, 5, 3),
                 text='canvas info',
                 waittime=400,
                 wraplength=250):
        self.waittime = waittime  # in miliseconds, originally 500
        self.wraplength = wraplength  # in pixels, originally 180
        self.canvas = canvas
        self.text = text
        self.canvas.tag_bind(tag_or_id, "<Enter>", self.onEnter)
        self.canvas.tag_bind(tag_or_id, "<Leave>", self.onLeave)
        self.canvas.tag_bind(tag_or_id, "<ButtonPress>", self.onLeave)
        self.bg = bg
        self.pad = pad
        self.id = None
        self.tw = None

    def onEnter(self, event=None):
        self.schedule()

    def onLeave(self, event=None):
        self.unschedule()
        self.hide()

    def schedule(self):
        self.unschedule()
        self.id = self.canvas.after(self.waittime, self.show)

    def unschedule(self):
        id_ = self.id
        self.id = None
        if id_:
            self.canvas.after_cancel(id_)

    def show(self, event=None):
        def tip_pos_calculator(canvas, label,
                               *,
                               tip_delta=(10, 5), pad=(5, 3, 5, 3)):

            c = canvas

            s_width, s_height = c.winfo_screenwidth(), c.winfo_screenheight()

            width, height = (pad[0] + label.winfo_reqwidth() + pad[2],
                             pad[1] + label.winfo_reqheight() + pad[3])

            mouse_x, mouse_y = c.winfo_pointerxy()

            x1, y1 = mouse_x + tip_delta[0], mouse_y + tip_delta[1]
            x2, y2 = x1 + width, y1 + height

            x_delta = x2 - s_width
            if x_delta < 0:
                x_delta = 0
            y_delta = y2 - s_height
            if y_delta < 0:
                y_delta = 0

            offscreen = (x_delta, y_delta) != (0, 0)

            if offscreen:

                if x_delta:
                    x1 = mouse_x - tip_delta[0] - width

                if y_delta:
                    y1 = mouse_y - tip_delta[1] - height

            offscreen_again = y1 < 0  # out on the top

            if offscreen_again:
                # No further checks will be done.

                # TIP:
                # A further mod might automagically augment the
                # wraplength when the tooltip is too high to be
                # kept inside the screen.
                y1 = 0

            return x1, y1

        bg = self.bg
        pad = self.pad
        canvas = self.canvas

        # creates a toplevel window
        self.tw = Toplevel(canvas.master)

        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)

        win = Frame(self.tw,
                       # background=bg,
                       borderwidth=0)
        label = Label(win,
                          text=self.text,
                          justify=LEFT,
                          background=bg,
                          relief=SOLID,
                          borderwidth=0,
                          wraplength=self.wraplength)

        label.grid(padx=(pad[0], pad[2]),
                   pady=(pad[1], pad[3]),
                   sticky=NSEW)
        win.grid()

        x, y = tip_pos_calculator(canvas, label)

        self.tw.wm_geometry("+%d+%d" % (x, y))

    def hide(self):
        if self.tw:
            self.tw.destroy()
        self.tw = None

if __name__=='__main__':
	app = App()
	while True:
		try:
			app.mainloop()
			break
		except UnicodeDecodeError:
			pass

	try:
		app.mainloop()
	except UnicodeDecodeError:
		severe( 'App encountered a UnicodeDecodeError when attempting to bind a \
<MouseWheel> event.  This is a known bug with Tcl/Tk 8.5 and can be fixed by \
changing a file in the Tkinter module in the python3 std libraries.  To make this \
change, copy the file `tkinter__init__.py` from this directory to the library for \
your standard system installation of python3.  For example, your command might \
look like this:\n\n\t$ cp ./tkinter__init__.py /Library/Frameworks/Python.\
frameworks/Versions/3.6/lib/python3.6/tkinter/__init__.py\n \
or\t$ cp ./tkinter__init__.py /usr/local/Frameworks/Python.framework/Versions/3.\
6/lib/python3.6/tkinter/__init__.py\nDepending on your python deployment.' )
