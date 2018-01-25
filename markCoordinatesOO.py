#!/usr/bin/env python3

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

class Crosshairs(object):
	def __init__(self, parent, x, y, save=True):
		trace = parent.traceSV.get()

		self.save = parent.writeCrosshairsToTraces

		self.selectedColor  = 'blue'
		self.unselectedColor= parent.getCurrentMetadata( 'traces' )[ trace ][ 'color' ]

		self.x,self.y = x,y
		self.canvas = parent.dicomImageCanvas # probably could do this more intelligently
		self.hline = self.canvas.create_line(x-_CROSSHAIR_LENGTH, y, x+_CROSSHAIR_LENGTH, y, fill=self.unselectedColor, width=_CROSSHAIR_UNSELECTED_WIDTH)
		self.vline = self.canvas.create_line(x, y-_CROSSHAIR_LENGTH, x, y+_CROSSHAIR_LENGTH, fill=self.unselectedColor, width=_CROSSHAIR_UNSELECTED_WIDTH)
		self.isSelected = False

		if trace not in parent.currentCrosshairs:
			parent.currentCrosshairs[ trace ] = []
		parent.currentCrosshairs[ trace ].append( self )

		if save:
			self.save()

	def getDistance(self, click):
		dx = abs( self.x - click[0] )
		dy = abs( self.y - click[1] )
		return math.sqrt( dx**2 + dy**2 )

	def select(self):
		self.canvas.itemconfig( self.hline, fill=self.selectedColor, width=_CROSSHAIR_SELECTED_WIDTH)
		self.canvas.itemconfig( self.vline, fill=self.selectedColor, width=_CROSSHAIR_SELECTED_WIDTH)
		self.isSelected = True

	def unselect(self):
		self.canvas.itemconfig( self.hline, fill=self.unselectedColor, width=_CROSSHAIR_UNSELECTED_WIDTH)
		self.canvas.itemconfig( self.vline, fill=self.unselectedColor, width=_CROSSHAIR_UNSELECTED_WIDTH)
		self.isSelected = False

	def undraw(self):
		self.canvas.delete( self.hline )
		self.canvas.delete( self.vline )

	def moveByIncr(self, dx, dy):
		self.x, self.y = self.x+dx, self.y+dy
		self.canvas.coords( self.hline, self.x-_CROSSHAIR_LENGTH, self.y, self.x+_CROSSHAIR_LENGTH, self.y )
		self.canvas.coords( self.vline, self.x, self.y-_CROSSHAIR_LENGTH, self.x, self.y+_CROSSHAIR_LENGTH )

		self.save()

	def recolor(self, color):
		oldColor = self.unselectedColor
		self.unselectedColor = color
		if self.isSelected == False:
			self.canvas.itemconfig( self.hline, fill=color )
			self.canvas.itemconfig( self.vline, fill=color )
		return oldColor

class markingGUI(Tk):
	def __init__(self):

		# need this first
		Tk.__init__(self)

		# require a $PATH and parse it
		parser = argparse.ArgumentParser()
		parser.add_argument('path', help='path (unique to a participant) where subdirectories contain raw data')
		args = parser.parse_args()

		# need to make sure we are given a valid path
		if os.path.exists( args.path ):
			self.path = args.path
			self.metadataFile = os.path.join( self.path, 'metadata.json' )
			self.metadata = self.getMetadata( self.metadataFile )
		else:
			print( "Error locating path: %s" % args.path )
			exit()

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
		self.currentImageID = None			# PhotoImage on the canvas, used to delete old stuff when we change images
		self.zoomFactor = 0					# make sure we don't zoom in/out too far
		self.isClicked = False
		self.isDragging = False
		self.currentCrosshairs = {}
		self.currentSelectedCrosshairs = set()
		self.undoQueue = []
		self.redoQueue = []
		self.availableTracesList = [ 'default' ]

		# declare string variables
		self.currentFileSV = StringVar(self)
		self.loadDicomSV = StringVar(self)
		self.frameSV = StringVar(self)
		self.traceSV = StringVar(self)
		self.newTraceSV = StringVar(self)

		# initialize string variables
		self.currentFileSV.set( self.files[ self.currentFID ] )
		self.frameSV.set( '1' )
		self.traceSV.set( _DEFAULT_TRACE_STYLE )
		self.newTraceSV.set( '' )

	def setupTk(self):
		self.geometry('1000x800')

		# ==============
		# playback frame:	to hold all of our soundfile/TextGrid functionality
		# ==============
		self.playbackFrame = Frame(self)
		self.playButton = Button(self.playbackFrame, text="Play/Pause", command=self.toggleAudio, state=DISABLED)

		# non playback stuff
		self.mainFrame = Frame(self)

		# ==============
		# control frame:	to hold all of our file navigation (w/in our given directory) functionality
		# ==============
		self.controlFrame = Frame(self.mainFrame)

		# display our currently selected filename
		self.participantFrame = Frame(self.controlFrame)

		# navigate between all available files in this directory
		self.navFileFrame = Frame(self.controlFrame)
		self.navFileLeftButton = Button(self.navFileFrame, text='<', command=self.navFileFramePanLeft)
		self.navFileJumpToMenu = OptionMenu(self.navFileFrame, self.currentFileSV, *self.files, command=self.navFileFrameJumpTo)
		self.navFileRightButton= Button(self.navFileFrame, text='>', command=self.navFileFramePanRight)

		# display information about files with this filename
		self.availableFilesFrame = Frame(self.controlFrame, width=200)
		self.availableFilesLabel1 = Label(self.availableFilesFrame, text='Available files:', justify=LEFT, pady=0)
		self.availableFilesList = Listbox(self.availableFilesFrame)

		# navigate between dicom frames
		self.navDicomFrame = Frame(self.controlFrame)
		self.navDicomLabel = Label(self.navDicomFrame, text="Choose a frame:")
		self.loadDicomButton = Button(self.navDicomFrame, text='Show DICOM', command=self.loadDicom)
		self.loadDicomLabel = Label(self.navDicomFrame, textvariable=self.loadDicomSV, pady=0)
		self.navDicomLeftButton = Button(self.navDicomFrame, text='<', command=self.navDicomFramePanLeft)
		self.navDicomEntryText = Entry(self.navDicomFrame, width=5, textvariable=self.frameSV)
		self.navDicomEntryButton = Button(self.navDicomFrame, text='Go', command=self.navDicomFrameEntry)
		self.navDicomRightButton= Button(self.navDicomFrame, text='>', command=self.navDicomFramePanRight)

		# navigate between tracings
		self.navTraceFrame = Frame(self.controlFrame)
		self.navTraceLabel = Label(self.navTraceFrame, text='Choose a trace:')
		self.navTraceNewFrame = Frame(self.navTraceFrame)
		self.navTraceNewTraceEntry = Entry(self.navTraceNewFrame, width=10, textvariable=self.newTraceSV)
		self.navTraceNewTraceButton = Button(self.navTraceNewFrame, text='Create', command=self.addNewTrace)
		self.navTraceMenu = OptionMenu(self.navTraceFrame, self.traceSV, *self.availableTracesList, command=self.changeTrace)
		self.navTraceButtonFrame = Frame(self.navTraceFrame)
		self.navTraceClearButton = Button(self.navTraceButtonFrame, text='Clear', command=self.clearTraces)
		self.navTraceColorButton = Button(self.navTraceButtonFrame, text='Recolor', command=self.changeTraceColor)
		self.navTraceSelectButton= Button(self.navTraceButtonFrame, text='Select', command=self.selectAllTrace)

		# ==============
		# ultrasound frame:	to hold our image
		# ==============
		self.ultrasoundFrame = Frame(self.mainFrame, bg='grey')
		self.dicomImageCanvas = Canvas(self.ultrasoundFrame, width=800, height=600)

		# pack all of our objects
		self.playbackFrame.pack(side=BOTTOM, fill=X, expand=0)
		self.playButton.pack()
		self.mainFrame.pack(side=BOTTOM, fill=BOTH, expand=1)
		self.controlFrame.pack(side=LEFT, fill=Y, expand=0)
		self.participantFrame.pack(expand=0)
		Label(self.participantFrame, text='Current participant:').pack()
		Label(self.participantFrame, text=self.metadata['participant']).pack()
		self.navFileFrame.pack(expand=0, pady=10)
		Label(self.navFileFrame, text="Choose a file:").pack()
		self.navFileLeftButton.pack(side=LEFT)
		self.navFileJumpToMenu.pack(side=LEFT)
		self.navFileRightButton.pack(side=LEFT)
		self.navDicomFrame.pack(pady=10)
		self.ultrasoundFrame.pack(side=LEFT, fill=BOTH, expand=1)
		self.dicomImageCanvas.pack()

		self.bind('<Left>', lambda a: self.navDicomFramePanLeft() )
		self.bind('<Right>', lambda a: self.navDicomFramePanRight() )
		self.bind('<Up>', lambda a: self.zoomIn() )
		self.bind('<MouseWheel>', self.zoom )
		self.bind('<Down>', lambda a: self.zoomOut() )
		self.bind('<space>', lambda a: self.toggleAudio() )
		self.bind('<BackSpace>', self.onBackspace )
		self.bind('<Escape>', self.onEscape )
		self.bind('<Control-z>', self.undo )
		self.bind('<Control-y>', self.redo )
		self.bind('<d>', lambda a: self.loadDicom() )
		self.bind('<Option-Left>', lambda a: self.navFileFramePanLeft() )
		self.bind('<Option-Right>', lambda a: self.navFileFramePanRight() )
		self.dicomImageCanvas.bind('<Button-1>', self.clickInCanvas )
		self.dicomImageCanvas.bind('<ButtonRelease-1>', self.unclickInCanvas )
		self.dicomImageCanvas.bind('<Motion>', self.mouseMoveInCanvas )

	def clickInCanvas(self, event):
		if self.dicom != None:

			self.click = (event.x, event.y)
			self.isDragging = False

			# see if we clicked near any existing crosshairs
			possibleSelections = {}
			if self.traceSV.get() in self.currentCrosshairs:
				for ch in self.currentCrosshairs[ self.traceSV.get() ]:
					d = ch.getDistance(self.click)
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

				# check if we're holding shift key
				if event.state != 1:
					# if not, clear current selection unselect crosshairs
					if self.currentSelectedCrosshairs != set():
						for sch in self.currentSelectedCrosshairs:
							sch.unselect()
					self.currentSelectedCrosshairs = set()

				# add this guy to our current selection
				ch.select()
				self.currentSelectedCrosshairs.add( ch )
				self.isDragging = True
				self.dragClick = self.click

			# if we didn't click near anything, place a new crosshairs
			else:
				# unselect crosshairs
				self.isClicked = True
				if self.currentSelectedCrosshairs != set():
					for sch in self.currentSelectedCrosshairs:
						sch.unselect()
				ch = Crosshairs( self, self.click[0], self.click[1] )
				self.undoQueue.append( {'type':'add', 'ch':ch })
				self.redoQueue = []

	def unclickInCanvas(self, event):
		if self.dicom != None:
			self.isDragging = False
			self.isClicked = False

	def mouseMoveInCanvas(self, event):
		if self.dicom != None:

			if self.isDragging:
				lastClick = self.dragClick
				thisClick = (event.x, event.y)
				dx = thisClick[0] - lastClick[0]
				dy = thisClick[1] - lastClick[1]
				for sch in self.currentSelectedCrosshairs:
					sch.moveByIncr( dx, dy )
				self.dragClick = thisClick
				#self.undoQueue.append({ 'type':'move', 'ch':ch, 'x'})

			elif self.isClicked:
				lastClick = self.click
				thisClick = (event.x, event.y)
				dx = abs(thisClick[0] - lastClick[0])
				dy = abs(thisClick[1] - lastClick[1])
				if dx > _CROSSHAIR_DRAG_BUFFER or dy > _CROSSHAIR_DRAG_BUFFER:
					self.click = thisClick
					ch = Crosshairs( self, self.click[0], self.click[1] )
					self.undoQueue.append({ 'type':'add', 'ch':ch })
					self.redoQueue = []

	def removeCrosshairs(self, ch):
		ch.undraw()
		trace = self.traceSV.get()
		if ch in self.currentCrosshairs[ trace ]:
			self.currentCrosshairs[ trace ].remove( ch )
			self.writeCrosshairsToTraces()
		self.currentSelectedCrosshairs = set()

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
			self.undoQueue.append({ 'type':'delete', 'x':sch.x, 'y':sch.y })
			self.redoQueue = []

	def undo(self, event):
		if len(self.undoQueue):
			action = self.undoQueue.pop()
			if action['type'] == 'add':
				ch = action['ch']
				self.removeCrosshairs( ch )
				self.redoQueue.append({ 'type':'delete', 'x':ch.x, 'y':ch.y })
			elif action['type'] == 'delete':
				ch = Crosshairs( self, action['x'], action['y'] )
				self.redoQueue.append({ 'type':'add', 'ch':ch })
			elif action['type'] == 'clear':
				os.rename( action['backup'], self.metadataFile )
				self.metadata = self.getMetadata( self.metadataFile )
				self.readTracesToCrosshairs()
				self.redoQueue.append({ 'type':'restore', 'backup':action['backup'], 'trace':action['trace'] })
			elif action['type'] == 'recolor':
				self.changeTrace( action['trace'] )
				oldColor = self.changeTraceColor( action['color'] )
				self.redoQueue.append({ 'type':'recolor', 'trace':action['trace'], 'color':oldColor })

	def redo(self, event):
		if len(self.redoQueue):
			action = self.redoQueue.pop()
			if action['type'] == 'add':
				ch = action['ch']
				self.removeCrosshairs( ch )
				self.undoQueue.append({ 'type':'delete', 'x':ch.x, 'y':ch.y })
			elif action['type'] == 'delete':
				ch = Crosshairs( self, action['x'], action['y'] )
				self.undoQueue.append({ 'type':'add', 'ch':ch })
			elif action['type'] == 'restore':
				self.changeTrace( action['trace'] )
				backup = self.clearTraces()
			elif action['type'] == 'recolor':
				self.changeTrace( action['trace'] )
				oldColor = self.changeTraceColor( action['color'] )
				self.undoQueue.append({ 'type':'recolor', 'trace':action['trace'], 'color':oldColor })

	def clearTraces(self):
		# assume this was an accident ... so we want to backup the old metadata
		tmppath = os.path.join( self.metadata['path'], 'tmp' )
		if os.path.exists( tmppath ) == False:
			os.mkdir( tmppath )
		backupfile = os.path.join( tmppath, 'metadata_backup_%s.json' % str(datetime.datetime.now()).replace( ' ', '_' ) )
		shutil.copy2( self.metadataFile, backupfile )

		# now we remove all the traces
		trace = self.traceSV.get()

		if trace in self.currentCrosshairs:
			if len( self.currentCrosshairs[ trace ] ):
				self.undoQueue.append({ 'type':'clear', 'backup':backupfile, 'trace':trace })
				self.redoQueue = []
			while len( self.currentCrosshairs[ trace ] ):
				# by popping we will prevent removeCrosshairs() from entering its conditional
				ch = self.currentCrosshairs[ trace ].pop()
				self.removeCrosshairs( ch )
			self.writeCrosshairsToTraces()

		return backupfile

	def changeTraceColor(self, _color=None):
		trace = self.traceSV.get()
		oldColor = None

		if trace in self.currentCrosshairs:
			color = '#%06x' % random.randint(0, 0xFFFFFF) if _color==None else _color
			for ch in self.currentCrosshairs[ trace ]:
				oldColor = ch.recolor( color )
			traces = self.getCurrentMetadata( 'traces' )
			traces[ trace ][ 'color' ] = color
			self.setCurrentMetadata( 'traces', traces )
			if _color==None:
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
		newTraceName = self.newTraceSV.get() if _newTraceName==None else _newTraceName
		if newTraceName not in self.availableTracesList and len(newTraceName) > 0:
			if _newTraceName == None:
				traces = self.getCurrentMetadata( 'traces' )
				traces[ newTraceName ] = { 'color' : '#%06x' % random.randint(0, 0xFFFFFF) }
				self.setCurrentMetadata( 'traces', traces )
				self.changeTrace( newTraceName )
			self.availableTracesList.append( newTraceName )
			self.navTraceMenu.children['menu'].add_command(
				label=newTraceName,
				command=lambda t=newTraceName: self.changeTrace(t) )


	def writeCrosshairsToTraces(self):
		trace = self.traceSV.get()
		traces = self.getCurrentMetadata( 'traces' )
		traces[ trace ][ str(self.frame) ] = [ {'x':ch.x, 'y':ch.y} for ch in self.currentCrosshairs[trace] ]
		self.setCurrentMetadata( 'traces', traces )

	def readTracesToCrosshairs(self):
		for style in self.getCurrentMetadata( 'traces' ).keys():
			self.traceSV.set( style )
			try:
				for trace in self.getCurrentMetadata( 'traces' )[ style ][ str(self.frame) ]:
					Crosshairs( self, trace['x'], trace['y'], False )
			except KeyError:
				pass
		self.traceSV.set( _DEFAULT_TRACE_STYLE )

	def zoom(self, event):
		if event.delta > 0:
			self.zoomIn()
		else:
			self.zoomOut()

	def zoomIn(self):
		print( 'zoom in' )

	def zoomOut(self):
		print( 'zoom out' )

	def loadAudio(self, codec):
		if codec in self.getCurrentMetadata('all'):
			audiofile = self.getCurrentMetadata( codec )
			if audiofile != None:
				try:
					self.mixer.music.load( audiofile )
					self.currentAudio = audiofile
					self.isPaused = False
					return True
				except:
					print('unable to load file %s' % audiofile)

	def toggleAudio(self):
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
		self.currentFileSV.set( self.files[ self.currentFID ] )
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
		try:
			self.dicomImageCanvas.itemconfig( self.frame, state=HIDDEN )
		except:
			pass

		# check if we have audio to load
		self.currentAudio = None
		audioFallbacks = [ '.wav', '.flac', '.ogg', '.mp3' ]
		for codec in audioFallbacks:
			if self.loadAudio( codec ) == True:
				self.playButton.config( state=NORMAL )
				break

		self.loadDicomButton.pack()
		self.loadDicomLabel.pack_forget()

		self.navDicomLabel.pack_forget()
		self.navDicomLeftButton.pack_forget()
		self.navDicomEntryText.pack_forget()
		self.navDicomEntryButton.pack_forget()
		self.navDicomRightButton.pack_forget()

		self.navTraceFrame.pack_forget()
		self.navTraceLabel.pack_forget()
		self.navTraceNewFrame.pack_forget()
		self.navTraceNewTraceEntry.pack_forget()
		self.navTraceNewTraceButton.pack_forget()
		self.navTraceMenu.pack_forget()
		self.navTraceButtonFrame.pack_forget()
		self.navTraceClearButton.pack_forget()
		self.navTraceColorButton.pack_forget()
		self.navTraceSelectButton.pack_forget()

		# check if we can pan left
		if self.getCurrentMetadata('left') == None:
			self.navFileLeftButton['state'] = DISABLED
		else:
			self.navFileLeftButton['state'] = NORMAL

		# check if we can pan right
		if self.getCurrentMetadata('right') == None:
			self.navFileRightButton['state'] = DISABLED
		else:
			self.navFileRightButton['state'] = NORMAL

		# clear contents and build new listbox
		self.availableFilesList.delete(0, END)
		for key in self.getCurrentMetadata('all'):
			if key not in { 'left', 'right', 'traces' }:
				self.availableFilesList.insert(END, '%s:' % key )
				self.availableFilesList.insert(END, '\t%s' % self.getCurrentMetadata(key) )

		# bring our current TextGrid into memory if it exists
		tgfile = self.getCurrentMetadata('.TextGrid')
		if tgfile != None:
			self.textgrid = TextGrid( tgfile, self.currentFileSV.get() )

		# check if we have a dicom file to bring into memory
		if self.getCurrentMetadata('.dicom') == None:
			self.loadDicomButton['state'] = DISABLED
		else:
			self.loadDicomButton['state'] = NORMAL

	def navFileFramePanLeft(self):
		"""
		controls self.navFileLeftButton for panning between available files
		"""

		if self.getCurrentMetadata('left') != None:
			# change the index of the current file
			self.currentFID -= 1
			# update
			self.changeFilesUpdate()

	def navFileFramePanRight(self):
		"""
		controls self.navFileRightButton for panning between available files
		"""

		if self.getCurrentMetadata('right') != None:
			# change the index of the current file
			self.currentFID += 1
			# update
			self.changeFilesUpdate()

	def navFileFrameJumpTo(self, choice):
		self.currentFID = self.files.index( choice )
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

		if self.currentImageID != None:
			self.dicomImageCanvas.delete( self.currentImageID )
		self.dicomImage = self.getDicomImage( self.frame )
		self.currentImageID = self.dicomImageCanvas.create_image( (400,300), image=self.dicomImage )

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
				return ImageTk.PhotoImage( Image.fromarray(arr) )
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

		dicomfile = self.getCurrentMetadata('.dicom')
		self.loadDicomLabel.pack()

		try:
			# load the dicom using a library ...
			# ... but we only want to load this once and not on every different frame
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

			self.navDicomLabel.pack()
			self.navDicomLeftButton.pack(side=LEFT)
			self.navDicomEntryText.pack(side=LEFT)
			self.navDicomEntryButton.pack(side=LEFT)
			self.navDicomRightButton.pack(side=LEFT)

			self.navTraceFrame.pack(pady=10)
			self.navTraceLabel.pack()
			self.navTraceNewFrame.pack()
			self.navTraceNewTraceEntry.pack(side=LEFT)
			self.navTraceNewTraceButton.pack(side=LEFT)
			self.navTraceMenu.pack()
			self.navTraceButtonFrame.pack()
			self.navTraceClearButton.pack(side=LEFT)
			self.navTraceColorButton.pack(side=LEFT)
			self.navTraceSelectButton.pack(side=LEFT)

			self.addNewTrace( _DEFAULT_TRACE_STYLE )
			for key in self.getCurrentMetadata( 'traces' ).keys():
				self.addNewTrace( key )
				self.availableTracesList.append( key )
			self.changeTrace( _DEFAULT_TRACE_STYLE )

			self.frames = self.dicom.pixel_array.shape[0]
			self.frame = 1

			self.loadDicomButton.pack_forget()
			self.loadDicomSV.set('Loaded %d frames.' % self.frames)

			self.changeFramesUpdate()

		except dicom.errors.InvalidDicomError:
			self.loadDicomSV.set('Error loading DICOM file.')

	def setCurrentMetadata(self, key, value):
		self.metadata[ 'files' ][ self.currentFileSV.get() ][ key ] = value
		with open( self.metadataFile, 'w' ) as f:
			json.dump( self.metadata, f, indent=3 )

	def getCurrentMetadata(self, key):
		"""
		returns data about the current file ... either everything or just a specfic key
		"""
		if key == 'all':
			return self.metadata['files'][ self.currentFileSV.get() ].keys()
		elif key in self.metadata['files'][ self.currentFileSV.get() ]:
			return self.metadata['files'][ self.currentFileSV.get() ][key]
		else:
			return None

	def getMetadata(self, mdfile):
		"""
		opens a metadata file (or creates one if it doesn't exist), recursively searches a directory
			for acceptable files, writes metadata back into memory, and returns the metadata object

		acceptable files: the metadata file requires matching files w/in subdirectories based on filenames
			for example, it will try to locate files that have the same base filename and
			each of a set of required extensions
		"""

		# either load up existing metadata
		if os.path.exists( mdfile ):
			print( "loading data from %s" % mdfile )
			with open( mdfile, 'r' ) as f:
				data = json.load( f )

		# or create new stuff
		else:
			print( "creating new datafile: %s" % mdfile )
			data = {
				'path': str(self.path),
				'participant': str(os.path.basename( os.path.normpath(self.path) )),
				'files': {} }

			# we want each object to have entries for everything here
			fileKeys = { 'left', 'right', '.dicom', '.flac', '.TextGrid', '.timetag', '.pycom' }
			files = {}

			# now get the objects in subdirectories
			for path, dirs, fs in os.walk( self.path ):
				for f in fs:
					# exclude some files explicitly here
					if f not in { 'metadata.json', }:
						fNoExt, fExt = os.path.splitext( f ) # e.g. 00.dicom -> 00, .dicom
						if fNoExt not in files:
							files[fNoExt] = { key:None for key in fileKeys }
						files[fNoExt][fExt] = os.path.join( path, f )

			# check that we find at least one file
			if len(files) == 0:
				print( 'Unable to find any files' )
				exit()

			# sort the files so that we can guess about left/right ... extrema get None/null
			# also add in the "traces" bit here
			left = None
			for key in sorted( files.keys() ):
				if left != None:
					files[left]['right'] = key
				files[key]['left'] = left
				left = key
				if 'traces' not in files[key]:
					files[key]['traces'] = { _DEFAULT_TRACE_STYLE:{ 'color':'red' } }

			# write
			data['files'] = files
			with open( mdfile, 'w' ) as f:
				json.dump( data, f, indent=3 )

		# and return it so that we can keep it in memory
		self.files = sorted(list(data['files'].keys()))
		return data















































	def old__init__(self):
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




if __name__ == "__main__":
	app = markingGUI()
	#app.after(500, traceClicks)
	#app.after(500, app.trackClicked)
	app.mainloop()
