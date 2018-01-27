#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from textgrid import TextGrid, IntervalTier, PointTier
from tkinter import *
from PIL import Image, ImageTk # pip install pillow

import numpy as np  # for manipulating dicom

import math	# might not need this
import sys	 # might not need this
import json
import os
import argparse
import dicom  # for manipulating dicom
import pygame # for playing music
import random
import datetime
import shutil

# some globals
_CROSSHAIR_LENGTH = 20
_CROSSHAIR_DRAG_BUFFER = 20
_CROSSHAIR_SELECT_RADIUS = 12
_CROSSHAIR_SELECTED_WIDTH = 3
_CROSSHAIR_UNSELECTED_WIDTH = 2
_DEFAULT_TRACE_STYLE = 'default'
_LOAD_ALL_DICOM_SLIDES = False

class AutoScrollbar(Scrollbar):
	def set(self, lo, hi):
		if float(lo) > 0.0 or float(hi) >= 1.0:
			Scrollbar.set(self, lo, hi)

class ZoomFrame(Frame):
	def __init__(self, master, delta, ):
		Frame.__init__(self, master, bg='blue')
		self.resetCanvas(master)

		self.delta = delta
		self.maxZoom = 5
		self.zoom = 0

	def resetCanvas(self, master):
		vScrollbar = AutoScrollbar( self, orient='vertical', command=self.scrollY )
		vScrollbar.grid(row=0, column=1, sticky='ns')

		self.canvas = Canvas( master, yscrollcommand=vScrollbar.set, bg='grey', width=800, height=600 )
		self.canvas.grid(row=0, column=0, sticky='news')
		self.canvas.update() # do i need

		self.master.rowconfigure(0, weight=1) # do i need
		self.master.columnconfigure(0, weight=1) # do i need

		self.canvas.bind('<Configure>', self.showImage ) # on canvas resize events
		self.canvas.bind('<Control-Button-1>', self.moveFrom )
		self.canvas.bind('<Control-B1-Motion>', self.moveTo )
		self.canvas.bind('<MouseWheel>', self.wheel ) # Windows & OSX
		self.canvas.bind('<Button-4>', self.wheel )   # Linux scroll up
		self.canvas.bind('<Button-5>', self.wheel )   # Linux scroll down

		self.origX = self.canvas.xview()[0] - 1
		self.origY = self.canvas.yview()[0] - 150

		self.imgscale = 1.0
		self.image = None

	def setImage(self, image): # expect an Image() instance
		self.image = image
		self.width, self.height = self.image.size
		self.container = self.canvas.create_rectangle(0,0,self.width,self.height,width=0)
		self.showImage()

	def showImage(self, event=None):
		if self.image != None:
			bbox1 = self.canvas.bbox( self.container )
			bbox1 = ( bbox1[0]+1, bbox1[1]+1, bbox1[2]-1, bbox1[3]-1 )
			bbox2 = ( self.canvas.canvasx(0), self.canvas.canvasy(0),
					  self.canvas.canvasx(self.canvas.winfo_width()),
					  self.canvas.canvasy(self.canvas.winfo_height()) )
			bbox = ( min(bbox1[0],bbox2[0]), min(bbox1[1],bbox2[1]), min(bbox1[2],bbox2[2]), min(bbox1[3],bbox2[3]) )
			if bbox[0] == bbox1[0] and bbox[2] == bbox1[2]:
				bbox = ( bbox1[0], bbox[1], bbox1[2], bbox[3] )
			if bbox[1] == bbox1[1] and bbox[3] == bbox1[3]:
				bbox = ( bbox[0], bbox1[1], bbox[2], bbox1[3] )
			self.canvas.configure(scrollregion=bbox)
			x1 = max(bbox2[0] - bbox1[0], 0)
			y1 = max(bbox2[1] - bbox1[1], 0)
			x2 = min(bbox2[2], bbox1[2]) - bbox1[0]
			y2 = min(bbox2[3], bbox1[3]) - bbox1[1]

			if int(x2 - x1) > 0 and int(y2 - y1) > 0:  # show image if it in the visible area
				x = min(int(x2 / self.imgscale), self.width)   # sometimes it is larger on 1 pixel...
				y = min(int(y2 / self.imgscale), self.height)  # ...and sometimes not
				image = self.image.crop((int(x1 / self.imgscale), int(y1 / self.imgscale), x, y))
				imagetk = ImageTk.PhotoImage( image.resize((int(x2 - x1), int(y2 - y1))) )
				imageid = self.canvas.create_image(max(bbox2[0], bbox1[0]), max(bbox2[1], bbox1[1]), anchor='nw', image=imagetk)
				self.canvas.lower(imageid)  # set image into background
				self.canvas.imagetk = imagetk  # keep an extra reference to prevent garbage-collection

			#self.master.update()

	def wheel(self, event):

		if self.image != None:
			x = self.canvas.canvasx(event.x)
			y = self.canvas.canvasy(event.y)
			bbox = self.canvas.bbox(self.container)  # get image area
			if bbox[0] < x < bbox[2] and bbox[1] < y < bbox[3]: pass  # Ok! Inside the image
			else: return  # zoom only inside image area
			scale = 1.0
			# Respond to Linux (event.num) or Windows (event.delta) wheel event
			if event.num == 5 or event.delta < 0:  # scroll down
				if self.zoom < self.maxZoom:
					self.zoom += 1
					i = min(self.width, self.height)
					if int(i * self.imgscale) > 30:
						self.imgscale /= self.delta
						scale        /= self.delta
					self.canvas.scale('all', x, y, scale, scale)  # rescale all canvas objects
			if event.num == 4 or event.delta > 0:  # scroll up
				if self.zoom > self.maxZoom * -1:
					self.zoom -= 1
					i = min(self.canvas.winfo_width(), self.canvas.winfo_height())
					if i > self.imgscale:
						self.imgscale *= self.delta
						scale        *= self.delta
					self.canvas.scale('all', x, y, scale, scale)  # rescale all canvas objects
			self.showImage()

	def scrollY(self, *args, **kwargs):
		self.canvas.yview(*args, **kwargs)
		self.showImage()

	def moveFrom(self, event):
		self.canvas.scan_mark( event.x, event.y )

	def moveTo(self, event):
		self.canvas.scan_dragto( event.x, event.y, gain=4 )
		self.showImage()

class Crosshairs(object):
	def __init__(self, parent, x, y, save=True, transform=True):

		trace = parent.traceSV.get()

		self.save = parent.writeCrosshairsToTraces

		self.zframe = parent.zframe
		self.canvas = self.zframe.canvas
		self.zoomAtBirth = self.zframe.zoom

		self.selectedColor  = 'blue'
		self.unselectedColor= parent.metadata.getTraceLevel( key='color' )

		self.origX, self.origY = x, y
		self.x, self.y = x, y
		if transform:
			self.x, self.y = self.transformCoords(x,y)
		self.defaultLength = _CROSSHAIR_LENGTH/2.0
		self.len = self.transformLength( self.defaultLength )

		self.hline = self.canvas.create_line(self.x-self.len, self.y, self.x+self.len, self.y, fill=self.unselectedColor, width=_CROSSHAIR_UNSELECTED_WIDTH)
		self.vline = self.canvas.create_line(self.x, self.y-self.len, self.x, self.y+self.len, fill=self.unselectedColor, width=_CROSSHAIR_UNSELECTED_WIDTH)
		self.isSelected = False
		self.isVisible = True
		self.hasChanged = transform

		if trace not in parent.currentCrosshairs:
			parent.currentCrosshairs[ trace ] = []
		parent.currentCrosshairs[ trace ].append( self )

		if save:
			self.save()

	def getAbsoluteCenter(self):
		if self.hasChanged:
			containerX, containerY = self.canvas.coords( self.zframe.container )[:2]
			absoluteX = (self.x-containerX) * self.zframe.delta**self.zoomAtBirth
			absoluteY = (self.y-containerY) * self.zframe.delta**self.zoomAtBirth
			self.origX, self.origY = absoluteX, absoluteY
			self.hasChanged = False
		else:
			absoluteX, absoluteY = self.origX, self.origY

		return absoluteX, absoluteY

	def transformCoords(self, x, y):
		x += self.canvas.canvasx(0)
		y += self.canvas.canvasy(0)
		return x,y

	def getCenter(self):
		coords = self.canvas.coords(self.hline)
		if len(coords) < 3:
			print(coords)
			print(self.hline)
			print(self.vline)
		coords = ( (coords[0]+coords[2])/2.0, coords[1] )
		return coords

	def transformLength(self, l):
		return l * self.zframe.imgscale

	def getDistance(self, click):
		if self.isVisible:
			click  = self.transformCoords(*click)
			coords = self.getCenter()
			dx = abs( coords[0] - click[0] )
			dy = abs( coords[1] - click[1] )
			return math.sqrt( dx**2 + dy**2 )
		else:
			return float('inf')

	def select(self):
		if self.isVisible:
			self.canvas.itemconfig( self.hline, fill=self.selectedColor, width=_CROSSHAIR_SELECTED_WIDTH)
			self.canvas.itemconfig( self.vline, fill=self.selectedColor, width=_CROSSHAIR_SELECTED_WIDTH)
			self.isSelected = True

	def unselect(self):
		if self.isVisible:
			self.canvas.itemconfig( self.hline, fill=self.unselectedColor, width=_CROSSHAIR_UNSELECTED_WIDTH)
			self.canvas.itemconfig( self.vline, fill=self.unselectedColor, width=_CROSSHAIR_UNSELECTED_WIDTH)
			self.isSelected = False

	def undraw(self):
		self.canvas.itemconfigure( self.hline, state='hidden' )
		self.canvas.itemconfigure( self.vline, state='hidden' )
		self.unselect()
		self.isVisible = False

	def draw(self):
		if self.isVisible == False:
			self.canvas.itemconfigure( self.hline, state='normal' )
			self.canvas.itemconfigure( self.vline, state='normal' )
			self.isVisible = True

	def dragTo(self, click):
		if self.isVisible:

			self.x, self.y = click
			self.len = self.transformLength( self.defaultLength )
			self.canvas.coords( self.hline, self.x-self.len, self.y, self.x+self.len, self.y )
			self.canvas.coords( self.vline, self.x, self.y-self.len, self.x, self.y+self.len )
			self.hasChanged = True

			self.save()

	def recolor(self, color):
		if self.isVisible:
			oldColor = self.unselectedColor
			self.unselectedColor = color
			if self.isSelected == False:
				self.canvas.itemconfig( self.hline, fill=color )
				self.canvas.itemconfig( self.vline, fill=color )
			return oldColor

class Metadata(object):
	def __init__(self, parent, path, backupmdfile=None):
		"""
		opens a metadata file (or creates one if it doesn't exist), recursively searches a directory
			for acceptable files, writes metadata back into memory, and returns the metadata object

		acceptable files: the metadata file requires matching files w/in subdirectories based on filenames
			for example, it will try to locate files that have the same base filename and
			each of a set of required extensions
		"""

		if os.path.exists( path ) == False:
			print( "Error locating path: %s" % path )
			exit(-1)

		self.parent = parent
		self.path = path

		self.mdfile = os.path.join( self.path, 'metadata.json' )

		# if we're trying to restore from a backup, copy its contents to our current mdfile location
		if backupmdfile != None:
			backupmdfilepath = os.path.join( self.path, backupmdfile )
			shutil.copy2( backupmdfilepath, self.mdfile )
			print( "restoring data from backup at %s" % backupmdfilepath)

		# either load up existing metadata
		if os.path.exists( self.mdfile ):
			print( "loading data from %s" % self.mdfile )
			with open( self.mdfile, 'r' ) as f:
				self.data = json.load( f )

		# or create new stuff
		else:
			print( "creating new datafile: %s" % self.mdfile )
			self.data = {
				'path': str(self.path),
				'participant': str(os.path.basename( os.path.normpath(self.path) )),
				'defaultTraceName': 'default',
				'defaultTraceColor': 'red',
				'files': {} }

			# we want each object to have entries for everything here
			fileKeys = { '_prev', '_next', '.dicom', '.flac', '.TextGrid', '.timetag', '.pycom' }
			files = {}

			# now get the objects in subdirectories
			for path, dirs, fs in os.walk( self.path ):
				for f in fs:
					# exclude some filetypes explicitly here
					fNoExt, fExt = os.path.splitext( f ) # e.g. 00.dicom -> 00, .dicom
					if fExt not in { '.json', }:
						if fNoExt not in files:
							files[fNoExt] = { key:None for key in fileKeys }
						files[fNoExt][fExt] = os.path.join( path, f )

			# check that we find at least one file
			if len(files) == 0:
				print( 'Unable to find any files' )
				exit()

			# sort the files so that we can guess about left/right ... extrema get None/null
			# also add in the "traces" bit here
			_prev = None
			for key in sorted( files.keys() ):
				if _prev != None:
					files[_prev]['_next'] = key
				files[key]['_prev'] = _prev
				_prev = key
				if 'traces' not in files[key]:
					files[key]['traces'] = { self.data['defaultTraceName'] : { 'color':self.data['defaultTraceColor'] } }
				files[key]['name'] = key

			# sort files and write to JSON
			self.data[ 'files' ] = [ files[key] for key in sorted(files.keys()) ]
			self.write()

		self.files = self.getFilenames()

	def write(self, _mdfile=None):
		mdfile = self.mdfile if _mdfile==None else _mdfile
		with open( mdfile, 'w' ) as f:
			json.dump( self.data, f, indent=3 )

	def writeBackup(self, _backupfile=None):

		# automatically generate backup filenames
		if _backupfile == None:
			# put backups in a ./tmp directory (relative to where the program was executed)
			backupdir = 'tmp'
			backuppath = os.path.join( self.path, backupdir )
			if os.path.exists( backuppath ) == False:
				os.mkdir( backuppath )

			# name backups by appending a timestamp to the filename
			backupfilename = 'metadata_backup_%s.json' % str(datetime.datetime.now()).replace( ' ', '_' )
			backupfilepath = os.path.join( backuppath, backupfilename )
			shutil.copy2( self.mdfile, backupfilepath )

			return os.path.join( backupdir, backupfilename )

		# unless we get explicitly told where to put it
		else:
			shutil.copy2( self.mdfile, os.path.join(self.path,_backupfile) )
			return _backupfile

	def getFilenames( self ):
		return [ f['name'] for f in self.data['files'] ]

	def getTopLevel( self, key ):
		if key in self.data.keys():
			return self.data[key]
		else:
			return None

	def setTopLevel( self, key, value ):

		self.data[ key ] = value
		self.write()

	def getFileLevel( self, key, _fileid=None ):

		fileid = self.parent.currentFID if _fileid==None else _fileid
		mddict = self.data[ 'files' ][ fileid ]

		if key == 'all':
			return mddict.keys()
		elif key in mddict:
			return mddict[ key ]
		else:
			return None

	def setFileLevel( self, key, value, _fileid=None ):

		fileid = self.parent.currentFID if _fileid==None else _fileid
		self.data[ 'files' ][ fileid ][ key ] = value
		self.write()

	def getTraceLevel( self, key=None, _fileid=None, _trace=None ):

		fileid = self.parent.currentFID if _fileid==None else _fileid
		trace = self.parent.traceSV.get() if _trace==None else _trace
		key = str(self.parent.frame) if key==None else key
		mddict = self.data[ 'files' ][ fileid ][ 'traces' ][ trace ]

		if key == 'all':
			return mddict # not mddict.keys()
		elif key == 'color':
			return mddict[ key ]
		elif key in mddict:
			return mddict[ key ]
		else:
			return None

	def setTraceLevel( self, key=None, value=None, _fileid=None, _trace=None ):

		fileid = self.parent.currentFID if _fileid==None else _fileid
		trace = self.parent.traceSV.get() if _trace==None else _trace
		key = str(self.parent.frame) if key==None else key
		mddict = self.data[ 'files' ][ fileid ][ 'traces' ]

		if trace not in mddict:
			mddict[ trace ] = {}
		self.data[ 'files' ][ fileid ][ 'traces' ][ trace ][ key ] = value

		self.write()

class markingGUI(Tk):
	def __init__(self):

		# need this first
		Tk.__init__(self)

		# require a $PATH and parse it
		parser = argparse.ArgumentParser()
		parser.add_argument('path', help='path (unique to a participant) where subdirectories contain raw data')
		args = parser.parse_args()

		self.metadata = Metadata( self, args.path )

		self.mixer = pygame.mixer
		self.mixer.init()

		self.setDefaults()
		self.setupTk()

		# populate everything
		self.changeFilesUpdate()

	def setDefaults(self):

		self.currentFID = 0 				# file index w/in list of sorted files
		self.currentAudio = None			# current audio
		self.isPaused = False
		self.frame = 0						# current frame of dicom file
		self.dicomImage = None  			# PhotoImage of the current dicom frame
		self.zoomFactor = 0					# make sure we don't zoom in/out too far
		self.isClicked = False
		self.isDragging = False
		self.currentCrosshairs = {}
		self.currentSelectedCrosshairs = set()
		self.undoQueue = []
		self.redoQueue = []
		self.availableTracesList = [ self.metadata.getTopLevel( 'defaultTraceName' ) ]

		# declare string variables
		self.currentFileSV = StringVar(self)
		self.loadDicomSV = StringVar(self)
		self.frameSV = StringVar(self)
		self.traceSV = StringVar(self)
		self.newTraceSV = StringVar(self)

		# initialize string variables
		self.currentFileSV.set( self.metadata.files[ self.currentFID ] )
		self.frameSV.set( '1' )
		self.traceSV.set( self.metadata.getTopLevel( 'defaultTraceName' ) )
		self.newTraceSV.set( '' )

	def setupTk(self):
		#self.geometry('1000x800')

		# ==============
		# playback frame:	to hold all of our soundfile/TextGrid functionality
		# ==============
		self.playbackFrame = Frame(self, bg='blue')
		self.playButton = Button(self.playbackFrame, text="Play/Pause", command=self.toggleAudio, state=DISABLED)

		# non playback stuff
		self.mainFrame = Frame(self)

		# ==============
		# control frame:	to hold all of our file navigation (w/in our given directory) functionality
		# ==============
		self.controlFrame = Frame(self.mainFrame)

		# display our currently selected filename
		self.participantFrame = Frame(self.controlFrame, pady=5)

		# navigate between all available files in this directory
		self.navFileFrame = Frame(self.controlFrame, pady=5)
		self.navFileLeftButton = Button(self.navFileFrame, text='<', command=self.navFileFramePanLeft)
		self.navFileJumpToMenu = OptionMenu(self.navFileFrame, self.currentFileSV, *self.metadata.files, command=self.navFileFrameJumpTo)
		self.navFileRightButton= Button(self.navFileFrame, text='>', command=self.navFileFramePanRight)

		# navigate between dicom frames
		self.navDicomFrame = Frame(self.controlFrame, pady=5)
		self.loadDicomButton = Button(self.navDicomFrame, text='Show DICOM', command=self.loadDicom)
		self.loadDicomLabel = Label(self.navDicomFrame, textvariable=self.loadDicomSV, pady=0)
		self.navDicomInnerFrame = Frame(self.navDicomFrame)
		self.navDicomLeftButton = Button(self.navDicomInnerFrame, text='<', command=self.navDicomFramePanLeft)
		self.navDicomEntryText = Entry(self.navDicomInnerFrame, width=5, textvariable=self.frameSV)
		self.navDicomEntryButton = Button(self.navDicomInnerFrame, text='Go', command=self.navDicomFrameEntry)
		self.navDicomRightButton= Button(self.navDicomInnerFrame, text='>', command=self.navDicomFramePanRight)
		self.navDicomLabel = Label(self.navDicomFrame, text="Choose a frame:")

		# navigate between tracings
		self.navTraceFrame = Frame(self.controlFrame, pady=5)
		self.navTraceLabel = Label(self.navTraceFrame, text='Choose a trace:')
		self.navTraceNewFrame = Frame(self.navTraceFrame)
		self.navTraceNewTraceEntry = Entry(self.navTraceNewFrame, width=10, textvariable=self.newTraceSV)
		self.navTraceNewTraceButton = Button(self.navTraceNewFrame, text='New', command=self.addNewTrace)
		self.navTraceMenuFrame = Frame(self.navTraceFrame)
		self.navTraceMenu = OptionMenu(self.navTraceMenuFrame, self.traceSV, *self.availableTracesList, command=self.changeTrace)
		self.navTraceRenameButton = Button(self.navTraceMenuFrame, text='Rename', command=self.renameTrace)
		self.navTraceButtonFrame = Frame(self.navTraceFrame)
		self.navTraceClearButton = Button(self.navTraceButtonFrame, text='Clear', command=self.clearTraces)
		self.navTraceColorButton = Button(self.navTraceButtonFrame, text='Recolor', command=self.changeTraceColor)
		self.navTraceSelectButton= Button(self.navTraceButtonFrame, text='Select', command=self.selectAllTrace)

		self.zoomResetButton = Button(self.controlFrame, text='Reset image', command=self.resetCanvas, pady=5 )

		# ==============
		# ultrasound frame:	to hold our image
		# ==============
		self.ultrasoundFrame = Frame(self.mainFrame)
		self.zframe = ZoomFrame(self.ultrasoundFrame, 1.3)

		# pack all of our objects
		self.mainFrame.grid()

		self.controlFrame.grid( row=0, sticky=N )

		self.participantFrame.grid( row=0, column=0 )
		Label(self.participantFrame, text='Current participant:').grid( row=0, column=0 )
		Label(self.participantFrame, text=self.metadata.getTopLevel('participant'), bg='lightgrey').grid( row=1, column=0 )

		self.navFileFrame.grid( row=1 )
		Label(self.navFileFrame, text="Choose a file:").grid( row=0, column=0, columnspan=3 )
		self.navFileLeftButton.grid( row=1, column=0 )
		self.navFileJumpToMenu.grid( row=1, column=1 )
		self.navFileRightButton.grid(row=1, column=2 )

		self.navDicomFrame.grid( row=2 )

		self.zoomResetButton.grid( row=3 )
		self.zframe.canvas.grid()

		#self.ultrasoundFrame.grid( row=0, column=1 )

		self.playbackFrame.grid( row=1, column=0, columnspan=2 )
		self.playButton.grid()

		self.bind('<Left>', lambda a: self.navDicomFramePanLeft() )
		self.bind('<Right>', lambda a: self.navDicomFramePanRight() )
		self.bind('<space>', self.toggleAudio )
		self.bind('<BackSpace>', self.onBackspace )
		self.bind('<Escape>', self.onEscape )
		self.bind('<Control-z>', self.undo )
		self.bind('<Control-y>', self.redo )
		self.bind('<Control-d>', lambda a: self.loadDicom() )
		self.bind('<Control-r>', lambda a: self.changeTraceColor() )
		self.bind('<Option-Left>', lambda a: self.navFileFramePanLeft() )
		self.bind('<Option-Right>', lambda a: self.navFileFramePanRight() )
		self.zframe.canvas.bind('<Button-1>', self.clickInCanvas )
		self.zframe.canvas.bind('<ButtonRelease-1>', self.unclickInCanvas )
		self.zframe.canvas.bind('<Motion>', self.mouseMoveInCanvas )

	def getCrosshairsInSelectRadius(self, click, trace):

		# see if we clicked near any existing crosshairs
		possibleSelections = {}
		if trace in self.currentCrosshairs:
			for ch in self.currentCrosshairs[ trace ]:
				d = ch.getDistance(click)
				if d < _CROSSHAIR_SELECT_RADIUS:
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

		# otherwise
		else:
			return None

	def clickInCanvas(self, event):
		if self.dicom != None:

			self.click = (event.x, event.y)
			self.isDragging = False

			# get nearby crosshairs from this trace
			nearby = self.getCrosshairsInSelectRadius( self.click, self.traceSV.get() )

			# if we didn't click near anything ...
			if nearby == None:

				# ... check our other traces to see if they contain any nearby guys
				for trace in self.availableTracesList:
					nearby = self.getCrosshairsInSelectRadius( self.click, trace )
					# if we got something
					if nearby != None:
						# switch to that trace and exit the loop
						self.changeTrace( trace )
						break

				# if still nothing, place a new crosshairs
				if nearby == None:
					# unselect crosshairs
					self.isClicked = True
					if self.currentSelectedCrosshairs != set():
						for sch in self.currentSelectedCrosshairs:
							sch.unselect()
					ch = Crosshairs( self, self.click[0], self.click[1] )
					self.undoQueue.append( {'type':'add', 'ch':ch })
					self.redoQueue = []

					return

			# only get here if we got a nearby guy somehow

			# if holding option key, unselect the guy we clicked on
			if event.state == 16:
				nearby.unselect()
				if nearby in self.currentSelectedCrosshairs:
					self.currentSelectedCrosshairs.remove( nearby )

			# otherwise, add it to our selection
			else:

				# check if we're holding shift key
				if event.state != 1 and nearby.isSelected == False:

					# if not, clear current selection
					if self.currentSelectedCrosshairs != set():
						for sch in self.currentSelectedCrosshairs:
							sch.unselect()
					self.currentSelectedCrosshairs = set()

				# add this guy to our current selection
				nearby.select()
				self.currentSelectedCrosshairs.add( nearby )

				# set dragging variables
				self.isDragging = True
				self.dragClick = self.click

	def unclickInCanvas(self, event):
		if self.dicom != None:
			if self.isDragging:
				dx = (event.x - self.click[0])
				dy = (event.y - self.click[1])
				self.undoQueue.append({ 'type':'move', 'chs':[ ch for ch in self.currentSelectedCrosshairs ], 'dx':-dx, 'dy':-dy })
				self.redoQueue = []
				self.writeCrosshairsToTraces()
			self.isDragging = False
			self.isClicked = False

	def mouseMoveInCanvas(self, event):
		if self.dicom != None:

			if self.isDragging:
				thisClick = (event.x, event.y)
				# move all currently selected crosshairs
				for sch in self.currentSelectedCrosshairs:
					# keep their relative distance constant
					center = sch.getCenter()
					newX = event.x + center[0] - self.dragClick[0]
					newY = event.y + center[1] - self.dragClick[1]
					sch.dragTo( (newX,newY) )

				self.dragClick = thisClick

			elif self.isClicked:
				lastClick = self.click
				thisClick = (event.x, event.y)
				dx = abs(thisClick[0] - lastClick[0]) / self.zframe.imgscale
				dy = abs(thisClick[1] - lastClick[1]) / self.zframe.imgscale
				if dx > _CROSSHAIR_DRAG_BUFFER or dy > _CROSSHAIR_DRAG_BUFFER:
					self.click = thisClick
					ch = Crosshairs( self, self.click[0], self.click[1] )
					self.undoQueue.append({ 'type':'add', 'ch':ch })
					self.redoQueue = []

	def removeCrosshairs(self, ch, write=True):
		ch.undraw()
		if write:
			self.writeCrosshairsToTraces()

	def onEscape(self, event):
		self.isDragging = False
		self.isClicked = False
		if self.currentSelectedCrosshairs != set():
			for sch in self.currentSelectedCrosshairs:
				sch.unselect()
		self.currentSelectedCrosshairs = set()

	def onBackspace(self, event):
		for sch in self.currentSelectedCrosshairs:
			self.removeCrosshairs( sch )
			self.undoQueue.append({ 'type':'delete', 'ch':sch })
			self.redoQueue = []
		self.currentSelectedCrosshairs = set()

	def undo(self, event):
		if len(self.undoQueue):

			action = self.undoQueue.pop()

			if action['type'] == 'add':
				ch = action['ch']
				self.removeCrosshairs( ch )
				self.redoQueue.append({ 'type':'delete', 'ch':ch })
			elif action['type'] == 'delete':
				ch = action['ch']
				ch.draw()
				self.redoQueue.append({ 'type':'add', 'ch':ch })
			elif action['type'] == 'move':
				for ch in action['chs']:
					ch.dragTo( action['dx'], action['dy'] )
				self.redoQueue.append({ 'type':'move', 'chs':action['chs'], 'dx':-action['dx'], 'dy':-action['dy'] })
			elif action['type'] == 'clear': # note this limits ability to undo `adds` and `deletes` later in the queue
				self.resetCanvas()
				self.restoreFromBackup( action['backup'] )
				self.readTracesToCrosshairs()
				self.redoQueue.append({ 'type':'restore', 'backup':action['backup'], 'trace':action['trace'] })
			elif action['type'] == 'recolor':
				self.changeTrace( action['trace'] )
				oldColor = self.changeTraceColor( action['color'] )
				self.redoQueue.append({ 'type':'recolor', 'trace':action['trace'], 'color':oldColor })
			elif action['type'] == 'rename':
				self.renameTrace( _newTraceName=action['old'], _oldTraceName=action['new'] ) # this is backwards on purpose
				self.redoQueue.append({ 'type':'rename', 'old':action['old'], 'new':action['new'] })
			else:
				print (action)
				raise NotImplementedError

			for sch in self.currentSelectedCrosshairs:
				sch.unselect()
			self.currentSelectedCrosshairs = set()

	def redo(self, event):
		if len(self.redoQueue):

			action = self.redoQueue.pop()

			if action['type'] == 'add':
				ch = action['ch']
				self.removeCrosshairs( ch )
				self.undoQueue.append({ 'type':'delete', 'ch':ch })
			elif action['type'] == 'delete':
				ch = action['ch']
				ch.draw()
				self.undoQueue.append({ 'type':'add', 'ch':ch })
			elif action['type'] == 'move':
				for ch in action['chs']:
					ch.dragTo( action['dx'], action['dy'] )
				self.undoQueue.append({ 'type':'move', 'chs':action['chs'], 'dx':-action['dx'], 'dy':-action['dy'] })
			elif action['type'] == 'restore': # note this truncates the redoQueue here
				self.changeTrace( action['trace'] )
				backup = self.clearTraces()
				self.undoQueue.append({ 'type':'clear', 'backup':action['backup'], 'trace':action['trace']})
			elif action['type'] == 'recolor':
				self.changeTrace( action['trace'] )
				oldColor = self.changeTraceColor( action['color'] )
				self.undoQueue.append({ 'type':'recolor', 'trace':action['trace'], 'color':oldColor })
			elif action['type'] == 'rename':
				self.renameTrace( _newTraceName=action['new'], _oldTraceName=action['old'] )
				self.undoQueue.append({ 'type':'rename', 'old':action['old'], 'new':action['new'] })
			else:
				print (action)
				raise NotImplementedError
			for sch in self.currentSelectedCrosshairs:
				sch.unselect()
			self.currentSelectedCrosshairs = set()

	def renameTrace(self, _newTraceName=None, _oldTraceName=None):

		# get our attempted old/new trace names
		newTraceName = self.newTraceSV.get() if _newTraceName==None else _newTraceName
		oldTraceName = self.traceSV.get() if _oldTraceName==None else _oldTraceName

		# reject if we already have a trace w/ this name for this file, we get an empty string, or we get no change
		if newTraceName not in self.availableTracesList and len(newTraceName) and newTraceName != oldTraceName:

			# if we're changing our default, change the default value
			if oldTraceName == self.metadata.getTopLevel( 'defaultTraceName' ):
				self.metadata.setTopLevel( 'defaultTraceName', newTraceName )

			# try to save the new trace name to all the files
			for fileid in range(len( self.metadata.files )):
				traces = self.metadata.getFileLevel( 'traces', _fileid=fileid )

				# check if we need to do any work
				# (should always be true, but just in case of manual editing of mdfiles)
				if oldTraceName in traces:

					# if the NEW trace name does not already exist for this file
					# (b/c we don't want to overwrite our own work)
					if newTraceName not in traces:
						# then do our rename and save
						traces[ newTraceName ] = traces.pop( oldTraceName )
						self.metadata.setFileLevel( 'traces', traces, _fileid=fileid )

			# if this was triggered by a button click, add it to the undoQueue
			if _newTraceName == None and _oldTraceName==None:
				self.undoQueue.append({ 'type':'rename', 'old':oldTraceName, 'new':newTraceName })
				self.redoQueue = []

			# update our current lists/variables
			self.changeTrace( newTraceName )
			self.availableTracesList.remove( oldTraceName )
			self.availableTracesList.append( newTraceName )

			# reset our dropdown menu
			menu = self.navTraceMenu.children['menu']
			menu.delete(0, END)
			for tracename in self.availableTracesList:
				menu.add_command( label=tracename, command=lambda t=tracename: self.changeTrace(t) )

	def clearTraces(self, _backupfile=None):

		# assume this was an accident ... so we want to backup the old metadata
		# (also used for restoring on `undo`)
		backupfile = self.metadata.writeBackup(_backupfile)

		# now we remove all the traces and save
		trace = self.traceSV.get()
		if trace in self.currentCrosshairs:
			for ch in self.currentCrosshairs[ trace ]:
				self.removeCrosshairs( ch, False )
			self.writeCrosshairsToTraces()

			# add to undoQueue if we did any work
			if len( self.currentCrosshairs[ trace ] ):
				self.undoQueue.append({ 'type':'clear', 'backup':backupfile, 'trace':trace })
				self.redoQueue = []

		return backupfile

	def changeTraceColor(self, _color=None):

		# since this command is bound to a key, don't want to execute if there's no dicom
		if self.dicom != None:

			# grab a new color if we weren't explicitly passed one
			# and also save our old color (for generating undoQueue stuff)
			newColor = self.getRandomHexColor() if _color==None else _color
			oldColor = self.metadata.getTraceLevel( 'color' )

			# write it out to all our files (incl. this one)
			for fileid in range(len( self.metadata.files )):
				self.metadata.setTraceLevel( key='color', value=newColor, _fileid=fileid )

			# recolor everything that's currently drawn to this trace
			trace = self.traceSV.get()
			for ch in self.currentCrosshairs[ trace ]:
				ch.recolor( newColor )

			# if this was triggered by a button click, add it to the undoQueue
			if _color == None:
				self.undoQueue.append({ 'type':'recolor', 'trace':trace, 'color':oldColor })
				self.redoQueue = []

			return oldColor

	def selectAllTrace(self):
		if self.traceSV.get() in self.currentCrosshairs:
			for ch in self.currentCrosshairs[ self.traceSV.get() ]:
				ch.select()
				self.currentSelectedCrosshairs.add( ch )

	def changeTrace(self, event):
		if event != self.traceSV.get():
			self.traceSV.set( event )
			self.newTraceSV.set( '' )
			for sch in self.currentSelectedCrosshairs:
				sch.unselect()
			self.currentSelectedCrosshairs = set()

	def addNewTrace(self, _newTraceName=None):

		# check if we're manually passing a name or whether this was from pressing the button (=None)
		newTraceName = self.newTraceSV.get() if _newTraceName==None else _newTraceName

		# don't want to add traces we already have or empty strings
		if newTraceName not in self.availableTracesList and len(newTraceName) > 0:

			# if this was from the button
			if _newTraceName == None:

				# choose a random color
				color = self.getRandomHexColor()

				# save the new trace name and color to all files
				for fileid in range(len( self.metadata.files )):
					traces = self.metadata.getFileLevel( 'traces', _fileid=fileid )
					traces[ newTraceName ] = { 'color':color }
					self.metadata.setFileLevel( 'traces', traces, _fileid=fileid )

				# switch to our newly added trace
				self.changeTrace( newTraceName )

			# keep track of what we've added so far
			self.availableTracesList.append( newTraceName )

			# and add it to the dropdown menu
			self.navTraceMenu.children['menu'].add_command(
				label=newTraceName,
				command=lambda t=newTraceName: self.changeTrace(t) )

	def writeCrosshairsToTraces(self):
		trace = self.traceSV.get()
		traces = self.metadata.getFileLevel( 'traces' )
		traces[ trace ][ str(self.frame) ] = []
		for ch in self.currentCrosshairs[trace]:
			if ch.isVisible:
				x,y = ch.getAbsoluteCenter()
				traces[ trace ][ str(self.frame) ].append({ 'x':x, 'y':y })
		self.metadata.setFileLevel( 'traces', traces )

	def readTracesToCrosshairs(self):
		traces = self.metadata.getFileLevel( 'traces' )
		for trace in traces:
			self.changeTrace( trace )
			try:
				for traceItem in traces[ trace ][ str(self.frame) ]:
					Crosshairs( self, traceItem['x'], traceItem['y'], transform=False, save=False )
			except KeyError:
				pass
		self.changeTrace( self.metadata.getTopLevel( 'defaultTraceName' ) )

	def resetCanvas(self):
		#if self.zframe.zoom < 0:
		#	for z in len(range( -self.frame.zoom )):
		self.zframe.resetCanvas( self.ultrasoundFrame )
		self.zframe.canvas.bind('<Button-1>', self.clickInCanvas )
		self.zframe.canvas.bind('<ButtonRelease-1>', self.unclickInCanvas )
		self.zframe.canvas.bind('<Motion>', self.mouseMoveInCanvas )
		self.zframe.zoom = 0
		self.changeFramesUpdate()


	def zoom(self, event):
		if event.delta > 0:
			self.zoomIn(event)
		else:
			self.zoomOut(event)

	def zoomIn(self, event):
		print( 'zoom in' )

	def zoomOut(self, event):
		print( 'zoom out' )

	def loadAudio(self, codec):
		audiofile = self.metadata.getFileLevel( codec )
		if audiofile != None:
			try:
				self.mixer.music.load( audiofile )
				self.currentAudio = audiofile
				self.isPaused = False
				return True
			except:
				print('unable to load file %s' % audiofile)

	def toggleAudio(self, event=None):
		if self.currentAudio != None:
			if self.isPaused:
				self.mixer.music.unpause()
				self.isPaused = False
			elif self.mixer.music.get_busy():
				self.mixer.music.pause()
				self.isPaused = True
			else:
				self.mixer.music.play()
				self.isPaused = False

	def changeFilesUpdate(self):

		# update the StringVars tracking the current file
		self.currentFileSV.set( self.metadata.files[ self.currentFID ] )
		self.loadDicomSV.set( '' )

		# reset other variables
		self.textgrid = None
		self.dicom = None
		self.frame = 1
		self.frames= 1
		self.currentImageID = None
		for trace in self.currentCrosshairs.keys():
			for ch in self.currentCrosshairs[ trace ]:
				ch.undraw()
		self.currentCrosshairs = {}
		self.currentSelectedCrosshairs = set()
		self.undoQueue = []
		self.redoQueue = []

		# check if we have audio to load
		self.currentAudio = None
		audioFallbacks = [ '.wav', '.flac', '.ogg', '.mp3' ]
		for codec in audioFallbacks:
			if self.loadAudio( codec ) == True:
				self.playButton.config( state=NORMAL )
				break

		self.loadDicomButton.grid()
		self.loadDicomLabel.grid_remove()

		self.navDicomLabel.grid_remove()
		self.navDicomLeftButton.grid_remove()
		self.navDicomEntryText.grid_remove()
		self.navDicomEntryButton.grid_remove()
		self.navDicomRightButton.grid_remove()

		self.navTraceFrame.grid_remove()
		self.navTraceLabel.grid_remove()
		self.navTraceNewFrame.grid_remove()
		self.navTraceNewTraceEntry.grid_remove()
		self.navTraceNewTraceButton.grid_remove()
		self.navTraceMenuFrame.grid_remove()
		self.navTraceMenu.grid_remove()
		self.navTraceRenameButton.grid_remove()
		self.navTraceButtonFrame.grid_remove()
		self.navTraceClearButton.grid_remove()
		self.navTraceColorButton.grid_remove()
		self.navTraceSelectButton.grid_remove()
		self.zoomResetButton.grid_remove()
		self.ultrasoundFrame.grid_remove()
		self.zframe.grid_remove()

		# check if we can pan left
		if self.metadata.getFileLevel( '_prev' ) == None:
			self.navFileLeftButton['state'] = DISABLED
		else:
			self.navFileLeftButton['state'] = NORMAL

		# check if we can pan right
		if self.metadata.getFileLevel( '_next' ) == None:
			self.navFileRightButton['state'] = DISABLED
		else:
			self.navFileRightButton['state'] = NORMAL

		# bring our current TextGrid into memory if it exists
		tgfile = self.metadata.getFileLevel( '.TextGrid' )
		if tgfile != None:
			self.textgrid = TextGrid( tgfile, self.currentFileSV.get() )

		# check if we have a dicom file to bring into memory
		if self.metadata.getFileLevel( '.dicom' ) == None:
			self.loadDicomButton['state'] = DISABLED
		else:
			self.loadDicomButton['state'] = NORMAL

	def navFileFramePanLeft(self):
		"""
		controls self.navFileLeftButton for panning between available files
		"""

		if self.metadata.getFileLevel( '_prev' ) != None:
			# change the index of the current file
			self.currentFID -= 1
			# update
			self.changeFilesUpdate()

	def navFileFramePanRight(self):
		"""
		controls self.navFileRightButton for panning between available files
		"""

		if self.metadata.getFileLevel( '_next' ) != None:
			# change the index of the current file
			self.currentFID += 1
			# update
			self.changeFilesUpdate()

	def navFileFrameJumpTo(self, choice):
		self.currentFID = self.metadata.files.index( choice )
		self.changeFilesUpdate()

	def changeFramesUpdate(self):

		# each frame should have its own crosshair objects
		for trace in self.currentCrosshairs.keys():
			for ch in self.currentCrosshairs[ trace ]:
				ch.undraw()
		self.currentCrosshairs = {}
		self.currentSelectedCrosshairs = set()
		self.undoQueue = []
		self.redoQueue = []

		self.dicomImage = self.getDicomImage( self.frame )
		self.zframe.imgscale = 1.0
		self.zframe.delta = 1.3
		self.zframe.zoom = 0
		self.zframe.setImage( self.dicomImage )
		#self.currentImageID = self.zframe.canvas.create_image( (400,300), image=self.dicomImage )

		# use our "traces" from our metadata to populate crosshairs for a given frame
		self.readTracesToCrosshairs()

		# check if we can pan left
		if self.frame == 1:
			self.navDicomLeftButton['state'] = DISABLED
		else:
			self.navDicomLeftButton['state'] = NORMAL

		# check if we can pan right
		if self.frame == self.frames:
			self.navDicomRightButton['state'] = DISABLED
		else:
			self.navDicomRightButton['state'] = NORMAL

		self.frameSV.set( str(self.frame) )

	def navDicomFramePanLeft(self):
		if self.dicom != None and self.frame > 1:
			self.frame -= 1
			self.changeFramesUpdate()

	def navDicomFramePanRight(self):
		if self.dicom != None and self.frame < self.frames:
			self.frame += 1
			self.changeFramesUpdate()

	def navDicomFrameEntry(self):
		try:

			choice = int( self.frameSV.get() )

			if choice<1:
				self.frame = 1
			elif choice>self.frames:
				self.frame = self.frames
			else:
				self.frame = choice

			self.changeFramesUpdate()

		except ValueError:
			pass

	def getDicomImage(self, frame):
		if _LOAD_ALL_DICOM_SLIDES:
			return self.dicomImages[frame]
		else:
			if len(self.dicom.pixel_array.shape) == 3: # greyscale
				arr = self.dicom.pixel_array.astype(np.float64)[ (frame-1),:,: ]
				return Image.fromarray(arr)
			elif len(self.dicom.pixel_array.shape) == 4: # RGB sampled ????
				arr = self.dicom.pixel_array.astype(np.float64)[ 0,(frame-1),:,: ]
				"""print( self.dicom.pixel_array.shape )
				print( arr.shape)
				arr = arr.swapaxes(0,2)
				print( arr.shape)
				arr = arr.swapaxes(0,1)"""
				print( arr.shape)
				return ImageTk.PhotoImage( Image.fromarray(arr))#, mode="RGB") )

	def loadDicom(self):
		"""
		brings a dicom file into memory if it exists
		"""

		# don't execute if dicom already loaded correctly
		if self.dicom == None:

			dicomfile = self.metadata.getFileLevel( '.dicom' )

			try:
				# load the dicom using a library
				self.dicom = dicom.read_file( dicomfile )
				self.frames = self.dicom.pixel_array.shape[0]

				if _LOAD_ALL_DICOM_SLIDES:
					self.dicomImages = [None] # have a dummy object so our frame index isn't off by 1
					for f in range(self.frames):
						# output progress
						self.loadDicomSV.set( ('Loading frame ' + str(f+1) + '...') )
						# flush
						self.update_idletasks()
						# convert the data to a numpy array, only keeping the frame-relevant pixel data
						arr = self.dicom.pixel_array.astype(np.float64)[f,:,:]
						# save a reference to it to avoid python garbage collection
						dicomImage = ImageTk.PhotoImage( Image.fromarray(arr) )
						self.dicomImages.append( dicomImage )

				# pack our widgets that require loaded dicom

				self.ultrasoundFrame.grid( row=0, column=1 )
				self.zframe.grid()

				self.navDicomLabel.grid( row=0 )

				self.navDicomInnerFrame.grid( row=1 )
				self.navDicomLeftButton.grid( row=0, column=0 )
				self.navDicomEntryText.grid( row=0, column=1 )
				self.navDicomEntryButton.grid( row=0, column=2 )
				self.navDicomRightButton.grid( row=0, column=3 )

				self.loadDicomLabel.grid( row=2 )

				self.navTraceFrame.grid( row=3 )
				self.navTraceLabel.grid( row=0 )
				self.navTraceNewFrame.grid( row=1 )
				self.navTraceNewTraceEntry.grid(  row=0, column=0 )
				self.navTraceNewTraceButton.grid( row=0, column=1 )
				self.navTraceMenuFrame.grid( row=2 )
				self.navTraceMenu.grid( row=0, column=0 )
				self.navTraceRenameButton.grid( row=0, column=1 )
				self.navTraceButtonFrame.grid( row=3 )
				self.navTraceClearButton.grid( row=0, column=0 )
				self.navTraceColorButton.grid( row=0, column=1 )
				self.navTraceSelectButton.grid(row=0, column=2 )

				self.zoomResetButton.grid( row=4 )

				# populate our traces list
				for key in self.metadata.getFileLevel( 'traces' ):
					self.addNewTrace( key )
				self.changeTrace( self.metadata.getTopLevel( 'defaultTraceName' ) )

				# reset frame count
				self.frame = 1

				# update status objects
				self.loadDicomButton.grid_remove()
				self.loadDicomSV.set('Loaded %d frames.' % self.frames)

				# populate everything else
				self.changeFramesUpdate()

			except dicom.errors.InvalidDicomError:
				self.loadDicomSV.set('Error loading DICOM file.')
				self.loadDicomLabel.grid()

	def restoreFromBackup(self, backup):
		self.metadata = Metadata( self, self.metadata.path, backup )

	def getRandomHexColor(self):
		return '#%06x' % random.randint(0, 0xFFFFFF)
















































if __name__ == "__main__":
	if False:
		root = Tk()
		path = './test/kik-EN/IM_0001.dicom'
		app = ZoomFrame( root )
		root.geometry( '800x600+1700+480' )
		app.mainloop()
	else:
		app = markingGUI()
		app.mainloop()


"""	def old__init__(self):
		self.setDefaults()

		self.className="mark points: %s" % self.filebase

		# bind buttons to actions
		self.canvas.bind("<Button-1>", self.onLeftClick)
		self.canvas.bind("<ButtonRelease-1>", self.onLeftUnClick)
		self.canvas.bind("<Motion>", self.onMouseMove)
		self.canvas.bind("<Delete>", self.onDelete)
		self.canvas.bind("<Tab>", self.onDelete)
		self.canvas.bind("<Down>", self.moveDown)
		self.canvas.bind("<Up>", self.moveUp)
		self.canvas.bind("<Left>", self.showPrev)
		self.canvas.bind("<Right>", self.showNext)
		self.canvas.bind("<Button-3>", lambda e: self.destroy())
		self.canvas.bind("<Escape>", lambda e: self.destroy())
		self.canvas.bind("<Button-4>", self.zoomImageOut)
		self.canvas.bind("<Button-5>", self.zoomImageIn)

		self.listbox = Listbox(self, height=3, selectmode=SINGLE)
		self.listbox.pack()

		# load and process file
		self.loadFile(self.measurementFn)
		self.afterLoad()

		self.populateSelector()
		self.subWindow = self.canvas.create_window((150,90),
			window=self.listbox, anchor="nw")

		self.canvas.focus_set()

	def setDefaults_____old(self):
		self.filebase = sys.argv[1]
		print(self.filebase)
		self.radius = 5
		self.click = None


		baselineStarts = {}
		baselineStarts["2014-10-09"] = (299,599-45)
		baselineStarts["2015-03-28"] = (250,532)
		baselineStarts["2015-04-25"] = (250,532)
		baselineStarts["2015-05-21"] = (268,530)
		baselineStarts["2015-11-13"] = (256,468)
		baselineStarts["2015-11-14"] = (281,491)
		baselineStarts["2016-01-20"] = (258,530)
		#baselineStarts["2015-09-10"] = (247,610)
		baselineStarts["2015-09-10"] = (264,529)
		#baselineStarts["2016-02-18"] = (247,613)
		baselineStarts["2016-02-18"] = (277,534)
		#baselineStarts["2016-02-19"] = (254,534) # one dot down
		baselineStarts["2016-02-19"] = (259,501)
		baselineStarts["2016-02-20"] = (272,497)
		baselineStarts["2016-03-16"] = (287,501)
		baselineEnds = {}
		baselineEnds["2014-10-09"] = (68,599-252)
		baselineEnds["2015-03-28"] = (68,370)
		baselineEnds["2015-04-25"] = (68,380)
		baselineEnds["2015-05-21"] = (68,342)
		baselineEnds["2015-11-13"] = (68,381)
		baselineEnds["2015-11-14"] = (68,298)
		baselineEnds["2016-01-20"] = (68,369) # a guess
		#baselineEnds["2015-09-10"] = (67,454) # a guess
		baselineEnds["2015-09-10"] = (67,304) # a guess
		baselineEnds["2016-02-18"] = (67,327) # a guess
		baselineEnds["2016-02-19"] = (67,322) # a guess
		baselineEnds["2016-02-20"] = (67,330) # a guess
		baselineEnds["2016-03-16"] = (67,320) # a guess
		TBreferences = {}
		TBreferences["2014-10-09"] = (425, 591)
		TBreferences["2015-03-28"] = (425, 591)
		TBreferences["2015-04-25"] = (425, 591)
		TBreferences["2015-05-21"] = (425, 591)
		TBreferences["2015-11-13"] = (425, 591)
		TBreferences["2015-11-14"] = (425, 591)
		TBreferences["2016-01-20"] = (425, 591)
		TBreferences["2015-09-10"] = (425, 591)
		TBreferences["2016-02-18"] = (425, 591)
		TBreferences["2016-02-19"] = (425, 591)
		TBreferences["2016-02-20"] = (425, 591)
		TBreferences["2016-03-16"] = (425, 591)

		# e.g., "2014-10-09" from
		#	   "/home/jonathan/q/dissertation/data/2014-10-09/bySlide"
		metafn = "dir.metadata"
		newmetafn = os.path.join("bySlide", metafn)
		#print(newmetafn)
		if os.path.exists(metafn):
			with open(metafn, 'r') as metadataFile:
				fileContents = metadataFile.read()
			metadata = json.loads(fileContents)
			curdir = metadata["date"]
		elif os.path.exists(newmetafn):
			with open(newmetafn, 'r') as metadataFile:
				fileContents = metadataFile.read()
			metadata = json.loads(fileContents)
			curdir = metadata["date"]
		else:
			curdirTuple = os.path.split(os.path.split(os.getcwd())[0])
			curdir = curdirTuple[1]
			if curdir not in baselineStarts:
				#last attempt
				curdir = os.path.split(os.path.split(curdirTuple[0])[1])[1]
			#print(curdir)

		if curdir in baselineStarts and curdir in TBreferences:
			#baselineStart = (299,599-45)
			#baselineEnd = (68,599-252)
			self.baselineStart = baselineStarts[curdir]
			self.baselineEnd = baselineEnds[curdir]
			reference = (self.baselineStart, self.baselineEnd)
			TRreference = reference
			TBreference = TBreferences[curdir]
			#TBreference = (425, 591)
		else:
			print("ERROR: date dir OR file to trace not found OR date dir not in TBreferences")
			sys.exit(-1)

		### format = {"TR": {'reference': ((x, y), (x, y)), 'userline': ((x, y), (x, y)), 'intersection': (x, y), 'measurement': x}}
		#fDictDefault = {'TR': {'reference': reference, 'type': 'vector'}, 'TB': {'type': 'point', 'reference': TBreference}}
		self.fDictDefault = {'TR': {'reference': reference, 'type': 'vector'}, 'TB': {'type': 'point', 'reference': TBreference}, 'trace': {'points': [], 'type': 'points'}}
		#Ey4Gekquc2Bv48v
		self.measurementFn = self.filebase+".measurement"
		#colours = {"TR": {"points": "MediumPurple1"}, "TB": {"dots": "lightgreen"}}
		self.colours = {"TR": {"points": "MediumPurple1"}, "TB": {"points": "SeaGreen1", "lines": "SeaGreen2", "references": "SteelBlue1"}, "trace": {"points": "Red"}} #IndianRed"}}

		self.whichImage = "main"
		self.zoomFactor = 2
		self.curZoomFactor = 1
		self.zoomed = False

		#image = Image.open(argv[1] if len(argv) >=2 else "018_516.png")
		self.image = PhotoImage(file=self.filebase+".png")
		self.scaledImage = PhotoImage(file=self.filebase+".png").zoom(self.zoomFactor)
		self.width = self.image.width()
		self.height = self.image.height()
		self.canvas = Canvas(self, width=self.width, height=self.height)
		self.canvas.pack()
		self.references = {}
		#image_tk = ImageTk.PhotoImage(image)
		self.slide = self.canvas.create_image(self.image.width()/2, self.image.height()/2, image=self.image)
		self.makeTRref()

		#global fDict
		self.lines = {}
		self.dots = {}
		self.points = {}
		self.stillClicked = False
		self.curCall = None
		self.paintDelay = 150 # in milliseconds
		self.prevPosition = (0, 0)
		self.distanceBuffer = 8
		self.prevSelection = None

		base = self.filebase.split("_")[0]
		nɛxt = int(self.filebase.split("_")[1])+1
		prev = int(self.filebase.split("_")[1])-1
		nextImageFn = "./adjacent/{}_{}.png".format(base, nɛxt)
		prevImageFn = "./adjacent/{}_{}.png".format(base, prev)
		if os.path.exists(nextImageFn) and os.path.exists(prevImageFn):
			self.nextImage = PhotoImage(file=nextImageFn)
			self.prevImage = PhotoImage(file=prevImageFn)
			self.nextImageScaled = PhotoImage(file=nextImageFn).zoom(self.zoomFactor)
			self.prevImageScaled = PhotoImage(file=prevImageFn).zoom(self.zoomFactor)
		else:
			print("WARNING: no previous and/or next frame images!")



	def zoomImageIn(self, event):
		#factor = 2
		if not self.zoomed:
			self.canvas.delete(self.slide)
			#scaledImage = self.image.subsample(2, 2)
			#print(factor)
			#self.scaledImage = PhotoImage(file=self.filebase+".png")#.zoom(factor)
			##self.canvas.scale("all", event.x, event.y, factor, factor)
			self.canvas.scale("all", 0, self.height, self.zoomFactor, self.zoomFactor)
			self.slide = self.canvas.create_image(self.image.width()*self.zoomFactor/2, 0, image=self.scaledImage)
			self.canvas.tag_lower(self.slide)
			self.canvas.pack()
			self.zoomed = True
			self.curZoomFactor = self.zoomFactor

		#self.image.scale("all", event.x, event.y, 1.1, 1.1)
		##self.image.zoom(1.1)
		#self.canvas.configure(scrollregion = self.canvas.bbox("all"))

	def zoomImageOut(self, event):
		#factor = 2
		if self.zoomed:
			self.canvas.delete(self.slide)
			self.canvas.scale("all", 0, self.height, 1/self.zoomFactor, 1/self.zoomFactor)
			self.slide = self.canvas.create_image(self.image.width()/2, self.image.height()/2, image=self.image)
			self.canvas.tag_lower(self.slide)
			#self.raiseStuff()
			self.canvas.pack()
			self.zoomed = False
			self.curZoomFactor = 1
		#self.canvas.scale("all", event.x, event.y, 0.9, 0.9)
		##self.image.scale("all", event.x, event.y, 0.9, 0.9)
		#self.canvas.configure(scrollregion = self.canvas.bbox("all"))

	def showNext(self, event):
		if self.whichImage != "next":
			self.canvas.delete(self.slide)
			if self.zoomed:
				self.slide = self.canvas.create_image(self.image.width()*self.zoomFactor/2, 0, image=self.nextImageScaled)
			else:
				self.slide = self.canvas.create_image(self.image.width()/2, self.image.height()/2, image=self.nextImage)

			self.canvas.tag_lower(self.slide)
			self.canvas.pack()
			self.whichImage = "next"
		else:
			self.resetImageToMain()

	def showPrev(self, event):
		if self.whichImage != "prev":
			self.canvas.delete(self.slide)
			if self.zoomed:
				self.slide = self.canvas.create_image(self.image.width()*self.zoomFactor/2, 0, image=self.prevImageScaled)
			else:
				self.slide = self.canvas.create_image(self.image.width()/2, self.image.height()/2, image=self.prevImage)
			self.canvas.tag_lower(self.slide)
			self.canvas.pack()
			self.whichImage = "prev"
		else:
			self.resetImageToMain()

	def resetImageToMain(self):
		self.canvas.delete(self.slide)
		if self.zoomed:
			self.slide = self.canvas.create_image(self.image.width()*self.zoomFactor/2, 0, image=self.scaledImage)
		else:
			self.slide = self.canvas.create_image(self.image.width()/2, self.image.height()/2, image=self.image)
		self.canvas.tag_lower(self.slide)
		self.canvas.pack()
		self.whichImage = "main"


	def makeTRref(self):
		self.references['TR'] = self.canvas.create_line(self.baselineStart[0], self.baselineStart[1], self.baselineEnd[0], self.baselineEnd[1], fill="blue")

	def listChange(self, event):
		#print("focus canvas")
		curMeasure = self.listbox.get(self.listbox.curselection())

		if curMeasure=='trace':
			self.hideStuff()
		else:
			if self.prevSelection=='trace':
				self.unHideStuff()

		self.prevSelection = curMeasure
		self.canvas.focus_set()

	def raiseStuff(self):
		for line in self.lines['TB']:
			self.canvas.tag_raise(line)
		self.canvas.tag_raise(self.lines['TR'])
		self.canvas.tag_raise(self.points['TR'])
		self.canvas.tag_raise(self.points['TB'])
		self.canvas.tag_raise(self.references['TR'])


	def hideStuff(self):
		#print("references", self.references)
		#print("lines", self.lines)
		#print("points", self.points)
		if 'TB' in self.lines:
			if self.lines['TB'] != None:
				for line in self.lines['TB']:
					self.canvas.delete(line)
		#print(self.points)
		self.canvas.delete(self.lines['TR'])
		self.canvas.delete(self.points['TR'])
		self.canvas.delete(self.points['TB'])
		self.canvas.delete(self.references['TR'])

	def unHideStuff(self):
		for measure in ['TR', 'TB']:
			self.makePoint(measure)
			#self.loadPoint(measure)
			#self.loadVector(measure)
			#print(self.fDict)

			#self.points[measure] = self.canvas.create_oval(thisX-self.radius, thisY-self.radius, thisX+self.radius, thisY+self.radius, outline=self.colours[measure]["points"])
		self.makeCrossHairs('TB')
		self.makeReference('TB')
		self.makeTRref()
		self.makeLine('TR')

	def moveDown(self, event):
		self.listbox.focus_set()
		current = self.listbox.curselection()[0]
		total = self.listbox.size()
		#print(current,total)
		if total > current+1:
			self.listbox.selection_clear(current)
			#self.listbox.activate(current + 1)
			#self.listbox.selection_set(0)
			self.listbox.selection_set(current + 1)
		#self.canvas.focus_set()

	def moveUp(self, event):
		self.listbox.focus_set()
		current = self.listbox.curselection()[0]
		if current > 0:
			self.listbox.selection_clear(current)
			#self.listbox.activate(current - 1)
			#self.listbox.selection_set(0)
			self.listbox.selection_set(current - 1)
		#self.canvas.focus_set()

	def populateSelector(self):
		for item in sorted(self.fDict):
			if item != "meta":
				self.listbox.insert(END, item)
		self.listbox.selection_set(0)
		#self.listbox.bind('<<ListboxSelect>>', self.listChange)
		self.listbox.bind('<ButtonRelease-1>', self.listChange)
		self.listbox.bind('<KeyRelease>', self.listChange)


	def line_intersection(self, line1, line2):
		xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
		ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

		def det(a, b):
			return a[0] * b[1] - a[1] * b[0]

		div = det(xdiff, ydiff)
		if div == 0:
			raise Exception('lines do not intersect')

		d = (det(*line1), det(*line2))
		x = det(d, xdiff) / div
		y = det(d, ydiff) / div
		return x, y


	def measurement2coordinates(self, source, end, distance):
		(sourceX, sourceY) = source
		(endX, endY) = end

		# calculate vector from source to end
		vectorX = float(endX - sourceX)
		vectorY = float(endY - sourceY)

		# calculate proportion of hypotenuse
		factor = distance / math.sqrt(vectorX * vectorX + vectorY * vectorY)

		# factor the lengths
		vectorX *= factor
		vectorY *= factor

		# calculate the new vector
		point = (int(sourceX + vectorX), int(sourceY + vectorY))

		return point

	def writeData(self): #fDict):
		with open(self.measurementFn, 'w') as measurementFile:
			measurementFile.write(json.dumps(self.fDict, sort_keys=True, indent=3))
		#print(fDict)

	def loadFile(self, fn):
		fDict = {}
		if os.path.isfile(fn):
			with open(fn, 'r') as dataFile:
				fileContents = dataFile.read()
			fType = type(json.loads(fileContents))
			# if it's an old-format file:
			if fType == float:
				print("old format file detected")
				measurement = json.loads(fileContents)
				intersection = self.measurement2coordinates(reference[0], reference[1], measurement)
				self.fDict = self.fDictDefault
				self.fDict['TR']['measurement'] = measurement
				self.fDict['TR']['intersection'] = intersection
				self.writeData() #fDict)
			# if it's a new-format file:
			elif fType == dict:
				self.fDict = json.loads(fileContents)
				for elemName in self.fDictDefault:
					if elemName not in self.fDict:
						print("{} not found in data; adding default".format(elemName))
						self.fDict[elemName] = self.fDictDefault[elemName]
		else:
			self.fDict = self.fDictDefault

	#return fDict

	def vectorClick(self, event, curMeasure, lastClick):
		lastDot = self.dots[curMeasure]
		self.dots[curMeasure] = self.canvas.create_oval(event.x-self.radius, event.y-self.radius, event.x+self.radius, event.y+self.radius, fill='red')
		if lastClick:
			if curMeasure in self.lines:
				self.canvas.delete(self.lines[curMeasure])
			self.lines[curMeasure] = self.canvas.create_line(lastClick[0], lastClick[1], self.click[0], self.click[1], fill='red')
			thislineStart = (lastClick[0], lastClick[1])
			thislineEnd = (self.click[0], self.click[1])
			thisLine = (thislineStart, thislineEnd)
			self.canvas.delete(lastDot)

			if curMeasure in self.points:
				self.canvas.delete(self.points[curMeasure])
			intersectionPoint = self.line_intersection(self.references[curMeasure], thisLine)
			self.points[curMeasure] = self.canvas.create_oval(intersectionPoint[0]-self.radius, intersectionPoint[1]-self.radius, intersectionPoint[0]+self.radius, intersectionPoint[1]+self.radius, outline=self.colours[curMeasure]["points"])
			#print(intersectionPoint)
			hypotenuse = math.hypot(intersectionPoint[0] - self.baselineStart[0], intersectionPoint[1] - self.baselineStart[1])
			#print(hypotenuse)
			self.fDict[curMeasure]['measurement'] = hypotenuse
			self.fDict[curMeasure]['intersection'] = intersectionPoint
			self.fDict[curMeasure]['userline'] = (thislineStart, thislineEnd)
			self.writeData() #self.fDict)

	def pointClick(self, event, curMeasure, lastClick):
		#print(points)
		#true_x = self.canvas.canvasx(event.x)
		#true_y = self.canvas.canvasy(event.y)
		#true_x = event.x/2
		#true_y = event.y/2
		#print(event.x, event.y)
		#print(true_x, true_y)
		lastPoint = self.points[curMeasure]
		self.points[curMeasure] = self.canvas.create_oval(event.x-self.radius*self.curZoomFactor, event.y-self.radius*self.curZoomFactor, event.x+self.radius*self.curZoomFactor, event.y+self.radius*self.curZoomFactor, outline=self.colours[curMeasure]["points"])
		#if lastClick:
		if curMeasure in self.lines:
			if self.lines[curMeasure] != None:
				for line in self.lines[curMeasure]:
					self.canvas.delete(line)
		self.canvas.delete(lastPoint)
		self.lines[curMeasure] = (
			self.canvas.create_line(event.x-50*self.curZoomFactor, event.y, event.x+50*self.curZoomFactor, event.y, fill=self.colours[curMeasure]["lines"]),
			self.canvas.create_line(event.x, event.y-50*self.curZoomFactor, event.x, event.y+50*self.curZoomFactor, fill=self.colours[curMeasure]["lines"])
		)
		intersectionPoint = (self.click[0], self.click[1])
		Dx = self.fDict[curMeasure]['reference'][0] - intersectionPoint[0]
		Dy = self.fDict[curMeasure]['reference'][1] - intersectionPoint[1]
		self.fDict[curMeasure]['intersection'] = intersectionPoint
		self.fDict[curMeasure]['measurement'] = (Dx, Dy)
		self.writeData() #self.fDict)

	#def traceClicks(self, event, curMeasure, lastClick):
	#	print("tracing?")
	#
	#	if self.stillClicked:
	#		print("hargle")
	#		#self.after(500, self.traceClicks(event, curMeasure, lastClick))

	def onMouseMove(self, event):
		if self.zoomed:
			self.click = (event.x/2, (self.height+event.y)/2)
		else:
			self.click = (event.x, event.y)

		if self.stillClicked:
			curPosition = self.click #(event.x, event.y)
			Dx = abs(event.x - self.prevPosition[0]) #*self.curZoomFactor
			Dy = abs(event.y - self.prevPosition[1]) #*self.curZoomFactor
			#print(Dx, Dy)
			if Dx > self.distanceBuffer*self.curZoomFactor or Dy > self.distanceBuffer*self.curZoomFactor:
				thisDiamond = self.create_diamond((event.x, event.y))
				#self.canvas.create_oval(event.x-self.radius, event.y-self.radius, event.x+self.radius, event.y+self.radius, fill='red')
				self.points['trace'].append(thisDiamond)
				self.references['trace'][thisDiamond] = curPosition
				self.fDict['trace']['points'].append(curPosition)  # FIXME: but different if zoomed
				self.writeData()
				self.prevPosition = (event.x, event.y)


	def create_diamond(self, centre):
		#print(centre)
		return self.canvas.create_polygon(centre[0]-self.radius*self.curZoomFactor, centre[1], centre[0], centre[1]+self.radius*self.curZoomFactor, centre[0]+self.radius*self.curZoomFactor, centre[1], centre[0], centre[1]-self.radius*self.curZoomFactor, fill='', outline=self.colours['trace']['points'])

	#def trackClicked(self, event):
		#print("tracing")
		#
		#if self.stillClicked:
		#	curPosition = (event.x, event.y)
		#	Dx = abs(curPosition[0] - self.prevPosition[0])
		#	Dy = abs(curPosition[1] - self.prevPosition[1])
		#	print(Dx, Dy)
		#	if Dx > self.distanceBuffer or Dy > self.distanceBuffer:
		#		self.canvas.create_oval(event.x-self.radius, event.y-self.radius, event.x+self.radius, event.y+self.radius, fill='red')
		#
		#	self.prevPosition = curPosition
		#	#self.curCall = self.after(self.paintDelay, self.trackClicked, event)

	def onLeftUnClick(self, event):
		self.stillClicked = False
		self.prevPosition = (0, 0)
		if self.curCall != None:
			self.after_cancel(self.curCall)

	def onDelete(self, event):
		curMeasure = self.listbox.get(self.listbox.curselection())
		curMeasureType = self.fDict[curMeasure]['type']

		if curMeasureType == "points":
			#print(self.references)
			if len(self.points['trace'])>=1:
				toDelete = self.points['trace'][-1]
				toDeletePt = self.references['trace'][toDelete]
				#print(toDelete)
				self.canvas.delete(toDelete)
				del self.points['trace'][-1]
				#print(toDeletePt)
				self.fDict['trace']['points'].remove(toDeletePt)
				self.writeData()

	def onLeftClick(self, event):
		curMeasure = self.listbox.get(self.listbox.curselection())
		curMeasureType = self.fDict[curMeasure]['type']
		#print(fDict)

		lastClick = self.click
		if self.zoomed:
			self.click = (event.x/2, (self.height+event.y)/2)
		else:
			self.click = (event.x, event.y)
		#print("clicked at: ", event.x, event.y)
		if curMeasureType == "vector":
			self.vectorClick(event, curMeasure, lastClick)

		elif curMeasureType == "point":
			self.pointClick(event, curMeasure, lastClick)

		#elif curMeasureType == "trace":
		#	#writeData(fDict)
		#	delay_ms=500
		#	time.sleep(delay_ms*0.001)
		#	print("nothing yet")
		elif curMeasureType == "points":
			self.stillClicked = True
			#self.traceClicks(event, curMeasure, lastClick)
			self.onMouseMove(event)

		else:
			print("undefined: {}".format(curMeasureType))

	def loadVector(self, measure):
		if "userline" in self.fDict[measure]:
			#print("BLER", measure)
			self.makeLine(measure)

		else:
			self.lines[measure] = None
		if "intersection" in self.fDict[measure]:
			(thisX, thisY) = self.fDict[measure]['intersection']
			self.points[measure] = self.canvas.create_oval(thisX-self.radius, thisY-self.radius, thisX+self.radius, thisY+self.radius, outline=self.colours[measure]["points"])
		else:
			self.points[measure] = None
		#if "reference" in self.fDict[measure]:
			#print("measure", measure)
			##self.references[measure] = self.fDict[measure]['reference']
			#self.references[measure] = "HARGLE" #self.fDict[measure]['reference']

	def makeReference(self, measure):
		#print("ref {}".format(measure))
		#print(self.fDict[measure]["reference"])
		(thisX, thisY) = self.fDict[measure]["reference"]
		self.references[measure] = self.canvas.create_oval(thisX-self.radius, thisY-self.radius, thisX+self.radius, thisY+self.radius, outline=self.colours[measure]["references"])

	def makePoint(self, measure):
		#if measure=="TB":
		#	hargle = "intersection"
		#	bargle = "points"
		#elif measure=="TR":
		#	hargle = "reference"
		#	bargle = "references"

		(thisX, thisY) = self.fDict[measure]["intersection"]
		#print(thisX, thisY, self.radius)
		self.points[measure] = self.canvas.create_oval(thisX-self.radius, thisY-self.radius, thisX+self.radius, thisY+self.radius, outline=self.colours[measure]["points"])

	def makeCrossHairs(self, measure):
		(thisX, thisY) = self.fDict[measure]["intersection"]
		self.lines[measure] = (
			self.canvas.create_line(thisX-50, thisY, thisX+50, thisY, fill=self.colours[measure]["lines"]),
			self.canvas.create_line(thisX, thisY-50, thisX, thisY+50, fill=self.colours[measure]["lines"])
		)
		#print("TB lines", self.lines['TB'])

	def makeLine(self, measure):
		if "userline" in self.fDict[measure]:
			((x1, y1), (x2, y2)) = self.fDict[measure]['userline']
			self.lines[measure] = self.canvas.create_line(x1, y1, x2, y2, fill='red')

	def loadPoint(self, measure):
		#print("loadPoint", measure, self.fDict[measure])
		#print(self.colours)
		if "intersection" in self.fDict[measure]:
			#if "lines" in self.colours[measure]:
			self.makePoint(measure)
#			(thisX, thisY) = self.fDict[measure]['intersection']
#			self.points[measure] = self.canvas.create_oval(thisX-self.radius, thisY-self.radius, thisX+self.radius, thisY+self.radius, outline=self.colours[measure]["points"])
			self.makeCrossHairs(measure)
#			self.lines[measure] = (
#				self.canvas.create_line(thisX-50, thisY, thisX+50, thisY, fill=self.colours[measure]["lines"]),
#				self.canvas.create_line(thisX, thisY-50, thisX, thisY+50, fill=self.colours[measure]["lines"])
#			)
		else:
			self.points[measure] = None
			self.lines[measure] = None

		if "reference" in self.fDict[measure]:
			self.makeReference(measure)
#			(thisX, thisY) = self.fDict[measure]['reference']
#			#print(thisX, thisY, self.radius)
#			self.references[measure] = self.canvas.create_oval(thisX-self.radius, thisY-self.radius, thisX+self.radius, thisY+self.radius, outline=self.colours[measure]["references"])
		else:
			self.references[measure] = None

	def loadPoints(self, measure):
		self.references[measure] = {}
		self.points[measure] = []
		for tracePt in self.fDict[measure]['points']:
			thisDiamond = self.create_diamond(tracePt)
			#self.references[measure]
			#if measure not in self.references:
			#
			if thisDiamond in self.references:
				print("¡PELIGRO!")
			self.references[measure][thisDiamond] = tracePt
			self.points[measure].append(thisDiamond)

	def afterLoad(self):
		# runs after loading the file, displays data from file
		for measure in self.fDict:
			#print(measure)
			#print(fDict[measure]['type'])
			if measure != "meta":
				#print(measure)
				if self.fDict[measure]['type'] == "vector":
					self.loadVector(measure)
				elif self.fDict[measure]['type'] == "point":
					self.loadPoint(measure)
				elif self.fDict[measure]['type'] == "points":
					self.loadPoints(measure)
				self.dots[measure] = None
				#print(self.references, self.points, self.lines, self.dots, measure)
"""
