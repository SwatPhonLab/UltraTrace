#!/usr/bin/env python3

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
warnings.showwarning = lambda msg, *args : print( 'WARNING: %s' % msg )

# critical dependencies
from magic import Magic # sudo -H pip3 install -U python-magic
getMIMEType = Magic(mime=True).from_file

# non-critical dependencies
try:
	import numpy as np				# sudo -H pip3 install -U numpy
	import pydicom as dicom 		# sudo -H pip3 install -U pydicom
	from PIL import Image, ImageTk, ImageEnhance, ImageDraw  # sudo -H pip3 install -U pillow
	_DICOM_LIBS_INSTALLED = True
except (ImportError):
	warnings.warn('Dicom library failed to load')
	_DICOM_LIBS_INSTALLED = False
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
	from textgrid import TextGrid, IntervalTier, PointTier, Point # sudo -H pip3 install -U textgrid
	_TEXTGRID_LIBS_INSTALLED = True
except (ImportError):
	warnings.warn('TextGrid library failed to load')
	_TEXTGRID_LIBS_INSTALLED = False
try:
	# import vlc
	# import tempfile
	# from multiprocessing import Process
	import threading, queue
	import time
	_VIDEO_LIBS_INSTALLED = True
except (ImportError):
	warnings.warn('VLC library failed to load')
	_VIDEO_LIBS_INSTALLED = False
try:
	#print('checking OS')
	import platform
	_PLATFORM = platform.system()
	print('Loading platform-specific enhancements for ' + _PLATFORM)
	if _PLATFORM == 'Linux':
		import xrp  # pip3 install xparser
		from ttkthemes import ThemedTk
		from pathlib import Path
	else:
		from ttkthemes import ThemedTk
except (ImportError):
	warnings.warn('Can\'t load platform-specific enhancements')
	_PLATFORM = 'generic'
	ThemedTk = Tk


# some globals
_CROSSHAIR_DRAG_BUFFER = 20
_CROSSHAIR_SELECT_RADIUS = 9#12
_TEXTGRID_ALIGNMENT_TIER_NAMES = [ 'frames', 'all frames', 'dicom frames', 'ultrasound frames' ]

class ZoomFrame(Frame):
	'''
	Wrapper for a Tk Frame() object that includes zooming and panning functionality.
	This code is inspired by the answer from https://stackoverflow.com/users/7550928/foo-bar
	at https://stackoverflow.com/questions/41656176/tkinter-canvas-zoom-move-pan ...
	Could probably be cleaned up and slimmed down
	'''
	def __init__(self, master, delta, app):
		Frame.__init__(self, master)
		self.app = app
		self.delta = delta
		self.maxZoom = 5
		#self.resetCanvas(master)

		self.canvas_width = 800
		self.width = 0
		self.canvas_height = 600
		self.height = 0
		self.shown = False
		self.aspect_ratio = 4.0/3.0

		self.canvas = Canvas( master,  bg='grey', width=self.canvas_width, height=self.canvas_height, highlightthickness=0 )
		self.canvas.grid(row=0, column=0, sticky='news')
		self.canvas.update() # do i need
		rect = RectTracker(self.canvas)
		rect.autodraw(outline='blue')

		# self.master.rowconfigure(0, weight=1) # do i need
		# self.master.columnconfigure(0, weight=1) # do i need

		# self.canvas.bind('<Configure>', self.showImage ) # on canvas resize events
		self.canvas.bind('<Control-Button-1>', self.moveFrom )
		self.canvas.bind('<Control-B1-Motion>', self.moveTo )
		self.canvas.bind('<MouseWheel>', self.wheel ) # Windows & Linux
		self.canvas.bind('<Button-4>', self.wheel )   # Linux scroll up
		self.canvas.bind('<Button-5>', self.wheel )   # Linux scroll down

		self.resetCanvas()

		self.canvas.bind('<Button-1>', self.app.onClickZoom )
		self.canvas.bind('<Motion>', self.app.onMotion )

		self.app.bind('<Command-equal>', self.wheel )
		self.app.bind('<Command-minus>', self.wheel )

	def resetCanvas(self):
		self.canvas_width = 800
		self.canvas_height = 600

		# self.canvas = Canvas( master,  bg='grey', width=self.canvas_width, height=self.canvas_height, highlightthickness=0 )
		# self.canvas.grid(row=0, column=0, sticky='news')
		# self.canvas.update() # do i need

		# self.master.rowconfigure(0, weight=1) # do i need
		# self.master.columnconfigure(0, weight=1) # do i need
		#
		# self.canvas.bind('<Configure>', self.showImage ) # on canvas resize events
		# self.canvas.bind('<Control-Button-1>', self.moveFrom )
		# self.canvas.bind('<Control-B1-Motion>', self.moveTo )
		# self.canvas.bind('<MouseWheel>', self.wheel ) # Windows & Linux FIXME
		# self.canvas.bind('<Button-4>', self.wheel )   # Linux scroll up
		# self.canvas.bind('<Button-5>', self.wheel )   # Linux scroll down

		self.origX = self.canvas.xview()[0] - 1
		self.origY = self.canvas.yview()[0] - 150

		self.zoom = 0
		self.imgscale = 1.0
		self.image = None
		self.panStartX = 0
		self.panStartY = 0
		self.panX = 0
		self.panY = 0

	def setImage(self, image): # expect an Image() instance
		self.image = image
		if self.width == 0:
			self.width, self.height = self.image.size
			self.aspect_ratio = self.width/self.height
		win_width = self.app.RIGHT.winfo_width()
		asp_height = round(win_width / self.aspect_ratio)
		win_height = self.app.RIGHT.winfo_height()
		asp_width = round(win_height * self.aspect_ratio)
		if asp_height > win_height:
			self.height = win_height
			self.width = asp_width
		else:
			self.height = asp_height
			self.width = win_width
		self.showImage()

	def showImage(self, event=None):
		# print(self.width, self.height, 'line 183')
		if self.image != None:
			self.canvas.delete('delendum')
			self.container = self.canvas.create_rectangle(0,0,self.width,self.height,width=0, tags='delendum')
			self.canvas.scale('all', 0, 0, self.imgscale, self.imgscale)
			self.canvas.move('all', self.panX, self.panY)
			bbox = self.canvas.bbox(self.container)
			image = self.image.resize((bbox[2] - bbox[0], bbox[3] - bbox[1]))
			imagetk = ImageTk.PhotoImage(image)
			image = self.canvas.create_image(bbox[0], bbox[1], anchor='nw', image=imagetk, tags='delendum')
			self.canvas.lower(image)
			self.canvas.imagetk = imagetk
			self.shown = True
			self.app.Trace.update()

	def wheel(self, event):
		if self.image != None:
			if event.keysym == 'equal' or event.keysym == 'minus': #what is this for?
				x = self.canvas_width/2
				y = self.canvas_height/2
			else:													#do these vars get used?
				x = self.canvas.canvasx(event.x)
				y = self.canvas.canvasy(event.y)

			# Respond to Linux (event.num) or Windows (event.delta) wheel event
			if event.num == 5 or event.delta < 0 or event.keysym == 'minus':  # zoom out
				if self.zoom < self.maxZoom:
					self.zoom += 1
					self.imgscale /= self.delta

			elif event.num == 4 or event.delta > 0 or event.keysym == 'equal':  # zoom in
				if self.zoom > self.maxZoom * -1:
					self.zoom -= 1
					self.imgscale *= self.delta

			bbox = self.canvas.coords(self.container)
			self.panX = bbox[0]
			self.panY = bbox[1]
			self.showImage()

	def scrollY(self, *args, **kwargs):
		self.canvas.yview(*args, **kwargs)
		self.showImage()

	def moveFrom(self, event):
		self.panStartX = event.x
		self.panStartY = event.y

	def moveTo(self, event):
		dx = event.x - self.panStartX
		dy = event.y - self.panStartY
		self.panStartX = event.x
		self.panStartY = event.y
		self.panX += dx
		self.panY += dy
		self.showImage()

class Header(Label):
	def __init__(self, master, text):
		'''
		Wrapper for Tk Label() object with a specified font
		'''
		Label.__init__(self, master, text=text, font='TkDefaultFont 12 bold')

class RectTracker:
	''' Copied from http://code.activestate.com/recipes/577409-python-tkinter-canvas-rectangle-selection-box/'''

	def __init__(self, canvas):
		self.canvas = canvas
		self.item = None

	def draw(self, start, end, **opts):
		"""Draw the rectangle"""
		return self.canvas.create_rectangle(*(list(start)+list(end)), **opts)

	def autodraw(self, **opts):
		"""Setup automatic drawing; supports command option"""
		self.start = None
		# self.canvas.bind("<Shift-Button-1>", self.__update, '+')
		self.canvas.bind("<Shift-B1-Motion>", self.__update, '+')
		self.canvas.bind("<ButtonRelease-1>", self.__stop, '+')

		self._command = opts.pop('command', lambda *args: None)
		self.rectopts = opts

	def __update(self, event):
		if not self.start:
			self.start = [event.x, event.y]
			# return

		if self.item is not None:
			self.canvas.delete(self.item)
		self.item = self.draw(self.start, (event.x, event.y), **self.rectopts)
		self._command(self.start, (event.x, event.y))

	def __stop(self, event):
		self.start = None
		self.canvas.delete(self.item)
		self.item = None

class Crosshairs(object):
	def __init__(self, zframe, x, y, color, transform=True):
		'''
		Crosshairs() serves two purposes:
		 	- handling (visual) placement of a `+` onto the zframe canvas
			- keeping track of point locations for saving/loading trace data

		@param
			zframe :	reference to the ZoomFrame containing the tracing canvas
			x :			x-canvas-coordinate of where we should place the center of the Crosshairs
			y :			y-canvas-coordinate of where we should place the center of the Crosshairs
			color :		color for when unselected
			transform : Boolean RE whether the coordinates need to be adjusted
		'''

		# keep a reference to the zframe
		self.zframe = zframe

		# set defaults here
		self.selectedColor  = 'blue'
		self.unselectedColor= color
		self.selectedWidth  = 1.5#3
		self.unselectedWidth= 1#2
		self.defaultLength  = _CROSSHAIR_SELECT_RADIUS

		# store position data
		self.x, self.y = x, y
		self.trueX, self.trueY = x, y
		if transform:
			self.trueX, self.trueY = self.transformCoordsToTrue(x, y)
		else:
			self.x, self.y = self.transformTrueToCoords(x, y)

		self.len = self.transformLength( self.defaultLength )
		# self.resetTrueCoords()
		self.isSelected = False
		self.isVisible = True

		# draw on the canvas
		self.hline = self.zframe.canvas.create_line(self.x-self.len, self.y, self.x+self.len, self.y, fill=self.unselectedColor, width=self.unselectedWidth)
		self.vline = self.zframe.canvas.create_line(self.x, self.y-self.len, self.x, self.y+self.len, fill=self.unselectedColor, width=self.unselectedWidth)

	# def resetTrueCoords(self):
	# 	'''
	# 	This function calculates the `true` coordinates for saving our crosshairs to the metadata file.
	# 	The values are calculated relative to the top left corner of the canvas at 1x zoom.  We need to
	# 	make sure to call this every time we change the position of a Crosshairs.
	# 	'''
	# 	#self.trueX, self.trueY = self.transformCoordsToTrue(self.x,self.y)
	# 	pass

	def getTrueCoords(self):
		''' called when we're saving to file '''
		return self.trueX, self.trueY

	def transformCoordsToTrue(self, x, y):
		'''
		canvas coords -> absolute coords
		absolute coords are % along each axis (e.g. center of image = [.5,.5])
		'''
		# x = (self.trueX - self.zframe.panX) / self.zframe.imgscale
		# y = (self.trueY - self.zframe.panY) / self.zframe.imgscale
		# return x,y
		truex = (x-self.zframe.panX)/(self.zframe.width*self.zframe.imgscale)
		truey = (y-self.zframe.panY)/(self.zframe.height*self.zframe.imgscale)
		# truex = (x-self.zframe.panX)/self.zframe.imgscale
		# truey = (y-self.zframe.panY)/self.zframe.imgscale
		# print(truex, truey)
		return truex, truey

	def transformTrueToCoords(self, truex, truey):
		'''
		absolute coords -> canvas coords
		absolute coords are % along each axis (e.g. center of image = [.5,.5])
		'''
		# x = (_x * self.zframe.imgscale) + self.zframe.panX
		# y = (_y * self.zframe.imgscale) + self.zframe.panY
		x = truex * self.zframe.width * self.zframe.imgscale + self.zframe.panX
		y = truey * self.zframe.height * self.zframe.imgscale + self.zframe.panY
		return x, y

	def transformCoords(self, x, y):
		''' transforms coordinates by the canvas offsets '''
		x += self.zframe.canvas.canvasx(0)
		y += self.zframe.canvas.canvasy(0)
		return x,y

	def transformLength(self, l):
		''' transforms a length by our current zoom-amount '''
		return l * self.zframe.imgscale

	def getDistance(self, click):
		''' calculates the distance from centerpoint to a click event '''
		click = self.transformCoords(*click)
		dx = abs( self.x - click[0] )
		dy = abs( self.y - click[1] )
		return math.sqrt( dx**2 + dy**2 ) if self.isVisible else float('inf') # invisible points infinitely far away

	def select(self):
		''' select this Crosshairs '''
		if self.isVisible:
			self.zframe.canvas.itemconfig( self.hline, fill=self.selectedColor, width=self.selectedWidth)
			self.zframe.canvas.itemconfig( self.vline, fill=self.selectedColor, width=self.selectedWidth)
			self.isSelected = True

	def unselect(self):
		''' stop selecting this Crosshairs '''
		if self.isVisible:
			self.zframe.canvas.itemconfig( self.hline, fill=self.unselectedColor, width=self.unselectedWidth)
			self.zframe.canvas.itemconfig( self.vline, fill=self.unselectedColor, width=self.unselectedWidth)
			self.isSelected = False

	def undraw(self):
		''' use this instead of deleting objects to make undos easier '''
		self.zframe.canvas.itemconfigure( self.hline, state='hidden' )
		self.zframe.canvas.itemconfigure( self.vline, state='hidden' )
		self.unselect()
		self.isVisible = False

	def draw(self):
		''' called when we undo a delete '''
		self.zframe.canvas.itemconfigure( self.hline, state='normal' )
		self.zframe.canvas.itemconfigure( self.vline, state='normal' )
		self.isVisible = True

	def dragTo(self, click):
		''' move the centerpoint to a given point (calculated in main class) '''
		if self.isVisible:

			self.x += (click[0] - self.x)
			self.y += (click[1] - self.y)
			# self.x, self.y = self.transformTrueToCoords(self.trueX, self.trueY)
			self.trueX, self.trueY = self.transformCoordsToTrue(self.x, self.y)
			self.len = self.transformLength( self.defaultLength )
			self.zframe.canvas.coords( self.hline, self.x-self.len, self.y, self.x+self.len, self.y )
			self.zframe.canvas.coords( self.vline, self.x, self.y-self.len, self.x, self.y+self.len )

	def recolor(self, color):
		''' change the fill color of the Crosshairs '''
		if self.isVisible:
			self.unselectedColor = color # change this in the background (i.e. don't unselect)
			if self.isSelected == False:
				self.zframe.canvas.itemconfig( self.hline, fill=color )
				self.zframe.canvas.itemconfig( self.vline, fill=color )

class MetadataModule(object):
	def __init__(self, app, path):
		'''
		opens a metadata file (or creates one if it doesn't exist), recursively searches a directory
			for acceptable files, writes metadata back into memory, and returns the metadata object

		acceptable files: the metadata file requires matching files w/in subdirectories based on filenames
			for example, it will try to locate files that have the same base filename and
			each of a set of required extensions
		'''
		print( ' - initializing module: Data')
		if path == None:
			app.update()
			path = filedialog.askdirectory(initialdir=os.getcwd(), title="Choose a directory")

		print( '   - parsing directory: `%s`' % path )

		if os.path.exists( path ) == False:
			print( "   - ERROR: `%s` could not be located" % path )
			exit(1)

		self.app = app
		self.path = path

		self.mdfile = os.path.join( self.path, 'metadata.json' )

		# either load up existing metadata
		if os.path.exists( self.mdfile ):
			print( "   - found metadata file: `%s`" % self.mdfile )
			with open( self.mdfile, 'r' ) as f:
				self.data = json.load( f )

		# or create new stuff
		else:
			if "trace.old files exist":
				"read the files"

			self.path = os.path.abspath(self.path)
			print( "   - creating new metadata file: `%s`" % self.mdfile )
			self.data = {
				'firstrun_path': self.path,
				'defaultTraceName': 'tongue',
				'traces': {
					'tongue': {
						'color': 'red',
						'files': {} } },
				'offset':0,
				'files': {} }

			# we want each object to have entries for everything here
			fileKeys = { '_prev', '_next', 'processed', 'offset' } # and `processed`
			MIMEs = {
				'audio/x-wav'		:	['.wav'],
				'audio/x-flac'		:	['.flac'],
				'audio/wav'		:	['.wav'],
				'audio/flac'		:	['.flac'],
				'application/dicom'	:	['.dicom'],
				'text/plain'		:	['.TextGrid']
			}
			files = {}

			# now get the objects in subdirectories
			for path, dirs, fs in os.walk( self.path ):
				for f in fs:
					# exclude some filetypes explicitly here by MIME type
					filepath = os.path.join( path, f )
					filename, extension = os.path.splitext( f )

					# allow us to follow symlinks
					real_filepath = os.path.realpath(filepath)

					#make file path relative to metadata file
					filepath = os.path.relpath(filepath,start=self.path)

					MIME = getMIMEType(real_filepath)
					if (MIME == 'text/plain' or MIME == 'application/json') and extension == '.measurement':
						print('Found old measurement file {}'.format(filename))
						self.importOldMeasurement(real_filepath, filename)
					elif MIME in MIMEs:
						# add `good` files
						if extension in MIMEs[ MIME ]:
							if filename not in files:
								files[filename] = { key:None for key in fileKeys }
							files[filename][extension] = filepath
					elif MIME == 'image/png' and '_dicom_to_png' in path:
						# check for preprocessed dicom files
						name, frame = filename.split( '_frame_' )
						#print(files)
						# if len(files) > 0:
						# might be able to combine the following; check
						if name not in files:
							files[name] = {'processed': None}
						if files[name]['processed'] == None:
							files[name]['processed'] = {}
						files[name]['processed'][str(int(frame))] = filepath

			# check that we find at least one file
			if len(files) == 0:
				print( '   - ERROR: `%s` contains no supported files' % path )
				exit()

			# sort the files so that we can guess about left/right ... extrema get None/null
			# also add in the "traces" bit here
			_prev = None
			for key in sorted( files.keys() ):
				if _prev != None:
					files[_prev]['_next'] = key
				files[key]['_prev'] = _prev
				_prev = key
				files[key]['name'] = key

			# sort files, set the geometry, and write
			self.data[ 'files' ] = [ files[key] for key in sorted(files.keys()) ]
			self.data[ 'geometry' ] = '1150x800+1400+480'
			self.write()

		self.app.geometry( self.getTopLevel('geometry') )
		self.files = self.getFilenames()

	def importOldMeasurement(self, filepath, filename):
		'''
		Writes information from .measurement file into metadata file
		'''
		#this is a hack -- should really go into Dicom (which is not yet loaded) and check
		defaultx = 800
		defaulty = 600

		open_file = json.load(open(filepath, 'r'))
		for key, value in open_file.items():
			if isinstance(value, dict):
				if 'type' in value.keys() and 'points' in value.keys():
					array = value['points']

		filenum, framenum = filename.split('_')
		# new_array = [{"x":point1/800,"y":point2/600} for point1, point2 in array]
		new_array = []
		for point1, point2 in array:
			#assuming traces were made at 1x zoom and no pan
			el = {"x":point1/defaultx,"y":point2/defaulty} #converts coords to "true" (i.e. % through each axis),
			new_array.append(el)
		list_of_files = self.data['traces']['tongue']['files']
		if not filenum in list_of_files:
			list_of_files[filenum]={}
		list_of_files[filenum][framenum] = new_array

	def write(self, _mdfile=None):
		'''
		Write metadata out to file
		'''
		# print()
		# print(self.data, 'write')
		# print()
		mdfile = self.mdfile if _mdfile==None else _mdfile
		with open( mdfile, 'w' ) as f:
			json.dump( self.data, f, indent=3 )

	def getFilenames( self ):
		'''
		Returns a list of all the files discovered from the initial directory traversal
		'''
		return [ f['name'] for f in self.data['files'] ]

	def getPreprocessedDicom( self, _frame=None ):
		'''
		Gets preprocessed (.dicom->.png) picture data for a given frame
		'''
		frame = self.app.frame if _frame==None else _frame #int(_frame)-1
		processed = self.getFileLevel( 'processed' )
		try:
			return self.unrelativize(processed[str(frame)])
		except: # catches missing frames and missing preprocessed data
			return None

	def getTopLevel( self, key ):
		'''
		Get directory-level metadata
		'''
		if key in self.data.keys():
			return self.data[key]
		else:
			return None

	def setTopLevel( self, key, value ):
		'''
		Set directory-level metadata
		'''
		self.data[ key ] = value
		self.write()

	def getFileLevel( self, key, _fileid=None ):
		'''
		Get file-level metadata
		'''
		fileid = self.app.currentFID if _fileid==None else _fileid
		mddict = self.data[ 'files' ][ fileid ]

		if key == 'all':
			return mddict.keys()
		elif key in mddict and mddict[ key ] != None:
			# if type(mddict[key]) is dict:
			# 	for el in mddict[key].keys():
			# 		mddict[key][el] = os.path.join(self.path, mddict[key][el])
			# else:
			# 	mddict[key] = os.path.join(self.path, mddict[key])
			# print(mddict[key])
			# print()
			return mddict[key]
		else:
			return None

	def unrelativize(self, fil):
		'''make from a relative path into non-relative path'''
		return os.path.join(self.path, fil)

	def setFileLevel( self, key, value, _fileid=None ):
		'''
		Set file-level metadata
		'''
		fileid = self.app.currentFID if _fileid==None else _fileid
		self.data[ 'files' ][ fileid ][ key ] = value
		self.write()

	def getCurrentFilename( self ):
		'''
		Helper function for interacting with traces
		'''
		return self.data[ 'files' ][ self.app.currentFID ][ 'name' ]

	def getCurrentTraceColor( self ):
		'''
		Returns color of the currently selected trace
		'''
		trace = self.app.Trace.getCurrentTraceName()
		if trace==None:
			return None
		return self.data[ 'traces' ][ trace ][ 'color' ]

	def setTraceColor( self, trace, color ):
		'''
		Set color for a particular trace name
		'''
		self.data[ 'traces' ][ trace ][ 'color' ] = color
		self.write()

	def getCurrentTraceAllFrames( self ):
		'''
		Returns a dictionary of with key->value give by frame->[crosshairs]
		for the current trace and file
		'''
		trace = self.app.Trace.getCurrentTraceName()
		filename = self.getCurrentFilename()
		try:
			return self.data[ 'traces' ][ trace ][ 'files' ][ filename ]
		except KeyError:
			return {}

	def getCurrentTraceTracedFrames(self):
		''' '''
		frames = self.getCurrentTraceAllFrames()
		tracedFrames = []
		for frame,traces in frames.items():
			if traces != []:
				tracedFrames.append(frame)
		return tracedFrames

	def getTraceCurrentFrame( self, trace ):
		'''
		Returns a list of the crosshairs for the given trace at the current file
		and current frame
		'''
		filename = self.getCurrentFilename()
		frame    = str(self.app.frame)# if _frame==None else str(_frame)
		try:
			return self.data[ 'traces' ][ trace ][ 'files' ][ filename ][ frame ]
		except KeyError:
			return []

	def setCurrentTraceCurrentFrame( self, crosshairs ):
		'''
		Writes an array of the current crosshairs to the metadata dictionary at
		the current trace, current file, and current frame
		'''
		trace = self.app.Trace.getCurrentTraceName()
		filename = self.getCurrentFilename()
		frame = self.app.frame
		if trace not in self.data[ 'traces' ]:
			self.data[ 'traces' ][ trace ] = { 'files':{}, 'color':None }
		if filename not in self.data[ 'traces' ][ trace ][ 'files' ]:
			self.data[ 'traces' ][ trace ][ 'files' ][ filename ] = {}
		self.data[ 'traces' ][ trace ][ 'files' ][ filename ][ str(frame) ] = crosshairs
		# print('line 701')
		self.write()

	def tracesExist( self, trace ):
		'''

		'''
		filename = self.getCurrentFilename()
		try:
			dict = self.data[ 'traces' ][ trace ][ 'files' ][ filename ]
			# print(dict)
			return [x for x in dict if dict[x] != []]
		except KeyError:
			return []

class TextGridModule(object):
	'''
	Manages all the widgets related to TextGrid files, including the tier name
	and the text content of that tier at a given frame
	'''
	def __init__(self, app):
		'''
		Keep a reference to the master object for binding the widgets we create
		'''
		print( ' - initializing module: TextGrid' )
		self.app = app
		self.frame = Frame(self.app.BOTTOM)
		self.label_padx = 0
		self.canvas_frame = Frame(self.app.BOTTOM)#, padx=self.label_padx)
		self.frame.grid( row=1, column=0, sticky=NE)
		self.canvas_frame.grid(row=1, column=1 )
		self.TextGrid = None
		self.selectedTier = StringVar()
		self.tg_zoom_factor = 1.5
		self.canvas_width=800
		self.canvas_height=60
		self.collapse_height=15
		self.selectedIntvlFrames = []
		self.selectedItem = None
		self.start = 0
		self.end = 0
		self.current = 0
		self.frame_shift = DoubleVar()

		self.startup()

		#bindings
		if _PLATFORM == 'Linux':
			self.app.bind("<Control-n>", self.getBounds)
			self.app.bind("<Control-a>", self.getBounds)
			self.app.bind("<Control-i>", self.getBounds)
			self.app.bind("<Control-o>", self.getBounds)
			self.app.bind("<Control-f>", self.openSearch)
			# Command is Alt in Linux, apparently
			self.app.bind("<Command-Up>", self.changeTiers)
			self.app.bind("<Command-Down>", self.changeTiers)
			self.app.bind("<Command-Left>", self.changeIntervals)
			self.app.bind("<Command-Right>", self.changeIntervals)
		elif _PLATFORM == 'Darwin':
			self.app.bind("<Command-n>", self.getBounds)
			self.app.bind("<Command-a>", self.getBounds)
			self.app.bind("<Command-i>", self.getBounds)
			self.app.bind("<Command-o>", self.getBounds)
			self.app.bind("<Command-f>", self.openSearch)
			self.app.bind("<Option-Up>", self.changeTiers)
			self.app.bind("<Option-Down>", self.changeTiers)
			self.app.bind("<Option-Left>", self.changeIntervals)
			self.app.bind("<Option-Right>", self.changeIntervals)
		#defaults (Command/Alt everything)
		else:
			self.app.bind("<Command-n>", self.getBounds)
			self.app.bind("<Command-a>", self.getBounds)
			self.app.bind("<Command-i>", self.getBounds)
			self.app.bind("<Command-o>", self.getBounds)
			self.app.bind("<Command-f>", self.openSearch)
			self.app.bind("<Command-Up>", self.changeTiers)
			self.app.bind("<Command-Down>", self.changeTiers)
			self.app.bind("<Command-Left>", self.changeIntervals)
			self.app.bind("<Command-Right>", self.changeIntervals)

		# these aren't Praat-like
		self.app.bind("<Shift-Left>", self.getBounds)
		self.app.bind("<Shift-Right>", self.getBounds)



	def startup(self):
		'''

		'''
		if _TEXTGRID_LIBS_INSTALLED:
			# default Label in case there are errors below
			self.TkWidgets = [{ 'label':Label(self.frame, text="Unable to load TextGrid file") }]
			# the Data module will pass this filename=None if it can't find an appropriate .TextGrid file
			filename = self.app.Data.getFileLevel( '.TextGrid' )
			# print(filename)
			if filename:
				try:
					# try to load up our TextGrid using the textgrid lib
					self.TextGrid = TextGrid.fromFile( self.app.Data.unrelativize(filename) )
				except:
					pass
			else:
				#print(self.app.Audio.duration)
				minTime = 0.
				maxTime = self.app.Audio.duration
				self.TextGrid = TextGrid(maxTime=self.app.Audio.duration)
				self.TkWidgets = []
				frameTime = self.app.Data.getFileLevel("FrameTime")
				numberOfFrames = self.app.Data.getFileLevel("NumberOfFrames")
				framesTier = PointTier(name="frames", maxTime=maxTime)
				if frameTime is not None and numberOfFrames is not None:
					for frameNum in range(1,numberOfFrames+1):
						pointTime = (frameTime*frameNum)/1000
						point = Point(pointTime,str(frameNum))
						framesTier.addPoint(point)
				else:
					for i, pointTime in enumerate([1.,2.,3.,4.]):
						point = Point(pointTime,str(i))
						framesTier.addPoint(point)
				self.TextGrid.tiers.append(framesTier)
				sentenceTier = IntervalTier("text")
				sentenceTier.add(minTime, maxTime, "text")
				self.TextGrid.tiers.append(sentenceTier)

			try:
				# reset default Label to actually be useful
				# self.TkWidgets = [{ 'label':Label(self.frame, text="TextGrid tiers:") }]
				self.TkWidgets = []
				# iterate the tiers
				self.frameTierName = self.getFrameTierName()
				self.app.frames = len(self.TextGrid.getFirst(self.frameTierName))
				for tier in self.TextGrid.getNames():
					if tier != self.frameTierName and tier != self.frameTierName + '.original':
						# make some widgets for each tier
						tierWidgets = self.makeTierWidgets( tier )
						self.TkWidgets.append( tierWidgets )
				#make other widgets
				self.makeFrameWidget()
				self.makeTimeWidget()
				#put items on canvases
				self.fillCanvases()
				#calculate first and last frames
				self.firstFrame = int(self.TextGrid.getFirst(self.frameTierName)[0].mark) + 1
				self.startFrame = self.firstFrame
				self.lastFrame = int(self.TextGrid.getFirst(self.frameTierName)[-1].mark) + 1
				self.endFrame = self.lastFrame
			except Exception as e:
				print("exception: ", e)
				pass

			self.grid()

	def reset(self, event=None):
		'''
		Try to load a TextGrid file based on information stored in the metadata
		'''
		# print(self.app.LEFT.winfo_width(), 'line 714')
		# for t in range(len(self.TkWidgets)):
		# 	tierWidgets = self.TkWidgets[t]
		# 	if 'canvas' in tierWidgets:
		# 		tierWidgets['canvas-label'].config(width=self.app.LEFT.winfo_width())
		# 		tierWidgets['canvas-label'].update()
		# 	if 'frames' in tierWidgets:
		# 		tierWidgets['frames-label'].config(width=self.app.LEFT.winfo_width())
		# print(self.pp)
		self.selectedIntvlFrames = []
		self.selectedItem = None
		#destroy
		# for wframe in [self.frame, self.canvas_frame]:
		# 	for child in wframe.winfo_children():
		# 		child.destroy()
		if _TEXTGRID_LIBS_INSTALLED:
			# default Label in case there are errors below
			# self.TkWidgets = [{ 'label':Label(self.frame, text="Unable to load TextGrid file") }]
			# the Data module will pass this filename=None if it can't find an appropriate .TextGrid file
			filename = self.app.Data.getFileLevel( '.TextGrid' )
			# print(filename)
			if filename:
				try:
					# try to load up our TextGrid using the textgrid lib
					self.TextGrid = TextGrid.fromFile( self.app.Data.unrelativize(filename) )
					# reset default Label to actually be useful
					# self.TkWidgets = [{ 'label':Label(self.frame, text="TextGrid tiers:") }]
					# self.TkWidgets = []
					# iterate the tiers
					self.frameTierName = self.getFrameTierName()
					self.app.frames = len(self.TextGrid.getFirst(self.frameTierName))
					# for tier in self.TextGrid.getNames():
					# 	if tier != self.frameTierName and tier != self.frameTierName + '.original':
					# 		# make some widgets for each tier
					# 		tierWidgets = self.makeTierWidgets( tier )
					# 		self.TkWidgets.append( tierWidgets )
					self.start = self.TextGrid.minTime
					self.end = self.TextGrid.maxTime
					self.current = self.TextGrid.getFirst(self.frameTierName)[self.app.frame-1].time
					#make other widgets
					# self.makeFrameWidget()
					#reset offset
					offset = self.app.Data.getFileLevel( 'offset' )
					if offset != None:
						self.frame_shift.set(offset)
					else:
						self.frame_shift.set(0)
					# self.makeTimeWidget()
					#put items on canvases
					self.fillCanvases()
					#calculate first and last frames
					self.firstFrame = int(self.TextGrid.getFirst(self.frameTierName)[0].mark) + 1
					self.startFrame = self.firstFrame
					self.lastFrame = int(self.TextGrid.getFirst(self.frameTierName)[-1].mark) + 1
					self.endFrame = self.lastFrame
				except:
					pass
			# self.grid()


	def shiftFrames(self):
		'''
		Replicate original TextGrid point tier (renamed [tiername].original)
		Shift points on TextGrid tier in accordance with self.frame_shift
			Shift value is relative to 0, i.e. inputting the same shift amount a second time will not change the shift
		Redisplay shifted points
		'''
		shift = self.frame_shift.get()
		if type(shift) == float:
			self.app.Data.setFileLevel( 'offset', shift )
			# diff = shift - self.app.Data.data['offset']
			originalTier = self.TextGrid.getFirst(self.frameTierName+'.original')
			if originalTier: pass
			else:
				orig = copy.deepcopy(self.TextGrid.getFirst(self.frameTierName))
				orig.name += '.original'
				self.TextGrid.append(orig)
				originalTier = self.TextGrid.getFirst(self.frameTierName+'.original')

			oldTier = self.TextGrid.getFirst(self.frameTierName)
			allPoints = oldTier[:]
			for point in allPoints:
				oldTier.removePoint(point)

			for point in originalTier:
				new_time = point.time + decimal.Decimal(shift/1000) ## NOTE: currently in ms
				if self.TextGrid.minTime <= new_time <= self.TextGrid.maxTime:
					self.TextGrid.getFirst(self.frameTierName).add(new_time, point.mark)

			# self.app.frames = len(self.TextGrid.getFirst(self.frameTierName))			#FIXME I feel like I shouldn't have to run the getFirst function every time, but I'm not sure when I have to go back to the original textgrid, and when I can just use a variable...
			self.firstFrame = int(self.TextGrid.getFirst(self.frameTierName)[0].mark) + 1
			self.lastFrame = int(self.TextGrid.getFirst(self.frameTierName)[-1].mark) + 1
			self.app.Data.data['offset'] = shift
			# self.frame_shift.set(shift)
			self.app.Data.write()
			# newTier.write(self.TextGrid.getFirst(self.frameTierName))
			self.fillCanvases()
			self.TextGrid.write(self.app.Data.unrelativize(self.app.Data.getFileLevel( '.TextGrid' )))


		#except ValueError:
		else:
			print('Not a float!')

	def makeTimeWidget(self):
		self.time_canvas = Canvas(self.canvas_frame, width=self.canvas_width, height=self.canvas_height/3, highlightthickness=0)
		s = self.time_canvas.create_text(3,0, anchor=NW, text=self.start)
		e = self.time_canvas.create_text(self.canvas_width,0, anchor=NE, text=self.end)
		c = self.time_canvas.create_text(self.canvas_width/2,0, anchor=N, text=self.current)
		self.TkWidgets.append({'times':self.time_canvas})

	def makeFrameWidget(self):
		'''
		makes frame widget
		'''
		#make regular frame stuff -- label and tier
		self.frames_canvas = Canvas(self.canvas_frame, width=self.canvas_width, height=self.canvas_height, background='gray', highlightthickness=0)
		frames_label = Canvas(self.frame, width=self.label_width, height=self.canvas_height, highlightthickness=0, background='gray')
		frames_label.create_text(self.label_width,0, anchor=NE, justify=CENTER,
								 text='frames: ', width=self.label_width, activefill='blue')

		# make subframe to go on top of label canvas
		sbframe = Frame(frames_label)
		#put new widgets onto subframe
		offset = self.app.Data.getFileLevel( 'offset' )
		if offset != None:
			self.frame_shift.set(offset)
		go_btn = Button(sbframe, text='Offset', command=self.shiftFrames, takefocus=0)
		# minmax = len(self.app.Audio.sfile)*1000
		txtbox = Spinbox(sbframe, textvariable=self.frame_shift, width=7, from_=-10000000, to=10000000)
		txtbox.bind('<Escape>', lambda ev: sbframe.focus())
		go_btn.grid(row=0, column=0, sticky=E)
		txtbox.grid(row=0, column=1, sticky=E)
		# put subframe on canvas
		window = frames_label.create_window(self.label_width*.3,self.canvas_height/3, anchor=NW, window=sbframe)

		self.TkWidgets.append({'name':self.frameTierName,'frames':self.frames_canvas,
							   'frames-label':frames_label})

		self.frames_canvas.bind("<Button-1>", self.getClickedFrame)

	def getFrameTierName(self):
		'''
		Handle some inconsistency in how we're naming our alignment tier
		'''
		for name in _TEXTGRID_ALIGNMENT_TIER_NAMES:
			if name in self.TextGrid.getNames():
				return name
		raise NameError( 'Unable to find alignment tier' )

	def getClickedFrame(self, event):
		'''
		Jumps to clicked frame
		'''
		item = self.my_find_closest(event.widget, event.x)
		self.setSelectedIntvlFrames((event.widget, item))
		frame = event.widget.gettags(item)[0][5:]
		self.app.frame = int(frame)
		if not frame in self.selectedIntvlFrames:
			self.selectedIntvlFrames = []
			self.wipeFill()
		self.app.framesUpdate()

	def makeTierWidgets(self, tier):
		'''
		Each tier should have two canvas widgets: `canvas-label` (the tier name),
		and `canvas` (the intervals on the tier with their marks)
		'''
		self.tier_pairs = {} #ends up being format {label: canvas}

		# self.app.Trace.frame.update()
		self.label_width=300#self.app.Trace.frame.winfo_width()+self.label_padx
		# print(self.label_width, 739)
		self.end = self.TextGrid.maxTime#float(self.TextGrid.maxTime)
		# self.first_frame = 1
		# print('line 805')
		# self.last_frame = self.TextGrid.getFirst(self.frameTierName)[-1].mark
		# print('line 807')
		tier_obj = self.TextGrid.getFirst(tier)
		widgets = { 'name':tier,
						 #'label':Label(self.frame, text=('- '+tier+':'), wraplength=200, justify=LEFT),
						 'canvas-label':Canvas(self.frame, width=self.label_width, height=self.canvas_height, highlightthickness=0),
						 # 'text' :Label(self.frame, text='', wraplength=550, justify=LEFT),
						 'canvas':Canvas(self.canvas_frame, width=self.canvas_width, height=self.canvas_height, background='gray', highlightthickness=0)}

		canvas = widgets['canvas']
		label = widgets['canvas-label']

		#builds tier label functionality
		label_text = label.create_text(self.label_width, self.canvas_height/2, anchor=E, justify=CENTER,
										text='temp', width=self.label_width/2, activefill='blue')

		canvas.bind("<Button-1>", self.genFrameList)
		label.bind("<Button-1>", self.genFrameList)
		label.bind("<Double-Button-1>", self.collapse)
		label.bind("<Button-4>", self.collapse)
		label.bind("<Button-5>", self.collapse)
		label.bind("<MouseWheel>", self.collapse)
		canvas.bind("<Button-4>", self.collapse)
		canvas.bind("<Button-5>", self.collapse)
		canvas.bind("<MouseWheel>", self.collapse)

		return widgets

	def changeIntervals(self,event):
		'''

		'''
		if self.selectedItem:
			duration = self.end - self.start

			# There might be a more efficient way to get the tier name:
			widg = self.selectedItem[0]
			itm = self.selectedItem[1]
			for el in self.TkWidgets:
				if widg in el.values():
					tier_name = el['name']
					break

			#finding Interval mintime and maxtime
			oldMinTime = None
			oldMaxTime = None
			q=0
			tags = widg.gettags(itm)
			while oldMinTime == None or oldMaxTime == None:
				if tags[q][:7] == 'minTime':
					oldMinTime = float(tags[q][7:])
				elif tags[q][:7] == 'maxTime':
					oldMaxTime = float(tags[q][7:])
				q+=1

			tier = self.TextGrid.getFirst(tier_name)
			intvl_i = tier.indexContaining(oldMaxTime-((oldMaxTime-oldMinTime)/2))

			if event.keysym == 'Left':
				new_intvl_i = intvl_i-1
			elif event.keysym == 'Right':
				new_intvl_i = intvl_i+1
			if 0 <= new_intvl_i < len(tier):
				#find characteristics of new adjacent interval
				newMinTime = tier[new_intvl_i].minTime
				newMaxTime = tier[new_intvl_i].maxTime
				itvlDuration = newMaxTime - newMinTime
				newCenter = newMinTime + itvlDuration/2

				#figure out new window parameters based on new interval
				start = newCenter - duration/2
				end = newCenter + duration/2
				if start < 0:
					self.start = 0
					self.end = duration
				elif end > self.TextGrid.maxTime:
					self.start = self.TextGrid.maxTime - duration
					self.end = self.TextGrid.maxTime
				else:
					self.start = newCenter - duration/2
					self.end = newCenter + duration/2
				relDuration = self.end - self.start

				# select new item
				rel_time = newCenter - self.start
				x_loc = float(rel_time/relDuration*self.canvas_width)
				item = self.my_find_closest(widg, x_loc)
				self.selectedItem = (widg, item)
				self.setSelectedIntvlFrames(self.selectedItem)

				self.fillCanvases()
				self.genFrameList(widg=widg, x_loc=x_loc)

	def changeTiers(self, event):
		'''

		'''
		index = None
		if self.selectedItem:
			for i, el in enumerate(self.TkWidgets):
				if self.selectedItem[0] in el.values():
					index = i

			if index != None:
				if event.keysym == 'Up' and 'canvas' in self.TkWidgets[index-1]:
					new_widg = self.TkWidgets[index-1]['canvas']
				elif event.keysym == 'Down' and 'canvas' in self.TkWidgets[index+1]:
					new_widg = self.TkWidgets[index+1]['canvas']
				else:
					return

				new_item = new_widg.find_withtag("frame"+str(self.app.frame))[0]
				self.selectedItem = (new_widg, new_item)

				self.fillCanvases()
				self.update()
				self.app.Spectrogram.update()

	def getMinMaxTime(self):
		'''
		Returns minTime and maxTime tags from selected interval
		If no minTime or maxTime, returns start or end time of viewed section of TextGrid
		'''
		start=None
		end=None

		for tag in self.selectedItem[0].gettags(self.selectedItem[1]):
			if tag[:7] == 'minTime':
				start = decimal.Decimal(tag[7:])
			elif tag[:7] == 'maxTime':
				end = decimal.Decimal(tag[7:])

		if start==None:
			start=self.start
		if end==None:
			end=self.end

		return (start,end)

	def getBounds(self, event):
		'''

		'''
		# print(event.char, event.keysym, event.keycode)
		# print(self.app.frame)
		f = decimal.Decimal(self.tg_zoom_factor)
		a = self.end - self.start
		z_out = (a-(a/f))/2
		z_in = ((f*a)-a)/2
		old_start = self.start
		old_end = self.end

		if event.keysym == 'n':
			if self.selectedItem:
				self.start, self.end = self.getMinMaxTime()
			# for tag in self.selectedItem[0].gettags(self.selectedItem[1]):
			# 	if tag[:7] == 'minTime':
			# 		self.start = decimal.Decimal(tag[7:])
			# 	elif tag[:7] == 'maxTime':
			# 		self.end = decimal.Decimal(tag[7:])
		if event.keysym == 'a':
			self.start = 0
			self.end = self.TextGrid.maxTime
		if event.keysym == 'o':
			self.start = self.start - z_in
			self.end = self.end + z_in
		if event.keysym == 'i':
			self.start = self.start + z_out
			self.end = self.end - z_out
		if event.keysym == 'Left':
			start = self.start - a/(10*f)
			end = self.end - a/(10*f)
			if (start < 0):
				self.start = 0
				self.end = a
			else:
				self.start = start
				self.end = end
		if event.keysym == 'Right':
			start = self.start + a/(10*f)
			end = self.end + a/(10*f)
			if end > self.TextGrid.maxTime:
				self.start = self.TextGrid.maxTime - a
				self.end = self.TextGrid.maxTime
			else:
				self.start = start
				self.end = end

		self.fillCanvases()

	def getTracedFrames(self,frames):
		'''

		'''
		frames = [frame[5:] for frame in frames] #to get rid of word "frame in tag"
		tracedFrames = []
		for trace in self.app.Data.data['traces']:
			tracedFrames = tracedFrames+self.app.Data.tracesExist(trace)

		return set(frames).intersection(tracedFrames)

	def fillCanvases(self):
		'''

		'''
		if self.start < 0:
			self.start = 0
		if self.end > self.TextGrid.maxTime:
			self.end = self.TextGrid.maxTime
		self.updateTimeLabels()

		if self.selectedItem:
			old_selected_tags = self.selectedItem[0].gettags(self.selectedItem[1])
		duration = self.end - self.start
		self.frameTier = self.TextGrid.getFirst(self.frameTierName)
		for el in self.TkWidgets:
			if 'name' in el:
				tier = self.TextGrid.getFirst(el['name'])
				# print(tier)
			if 'canvas' in el:
				canvas = el['canvas']
				#remove previous intervals
				canvas.delete(ALL)
				#get starting interval
				i = tier.indexContaining(self.start)
				time = tier[i].maxTime
				frame_i = 0
				while i < len(tier) and tier[i].minTime <= self.end:
					if self.start >= tier[i].minTime:
						strtime = self.start
					else:
						strtime = tier[i].minTime
					if self.end <= tier[i].maxTime:
						time = self.end
					length = time - strtime
					pixel_length = length/duration*self.canvas_width

					mod = length/2
					rel_time = time-self.start
					loc=(rel_time-mod)/duration*self.canvas_width

					text = canvas.create_text(loc, self.canvas_height/2, justify=CENTER,
										text=tier[i].mark, width=pixel_length, activefill='blue')
					minTimetag = "minTime"+str(tier[i].minTime)
					maxTimetag = "maxTime"+str(tier[i].maxTime)
					canvas.addtag_withtag(minTimetag, text)
					canvas.addtag_withtag(maxTimetag, text)
					#add containted frames to tags
					while frame_i < len(self.frameTier) and self.frameTier[frame_i].time <= tier[i].maxTime:
						if self.frameTier[frame_i].time >= tier[i].minTime:
							canvas.addtag_withtag("frame"+self.frameTier[frame_i].mark, text)
							if tier[i].mark != '':
								el['canvas-label'].addtag_all("frame"+self.frameTier[frame_i].mark)
						frame_i+=1
					#pass on selected-ness
					if self.selectedItem:
						if self.selectedItem[0] != self.app.Spectrogram.canvas:
							# old_selected_tags = self.selectedItem[0].gettags(self.selectedItem[1])
							if minTimetag in old_selected_tags and maxTimetag in old_selected_tags:
								self.selectedItem = (canvas, text)
					#create line
					loc=rel_time/duration*self.canvas_width
					i+=1
					if i < len(tier) and loc < self.canvas_width:
						canvas.create_line(loc,0,loc,self.canvas_height, tags='line')
						time = tier[i].maxTime #here so that loop doesn't run an extra time

				#fills labels with info about tiers w/traces
				self.updateTierLabels()

			elif 'frames' in el:
				frames = el['frames']
				i = 0
				frames.delete(ALL)
				first_frame_found = False
				while i < len(tier) and tier[i].time <= self.end :
					# print(tier[i].time, i,'frame time and frame number (line 1076)')
					if tier[i].time >= self.start:
						# x_coord = (tier[i].time-self.start)/duration*self.canvas_width
						x_coord = ((tier[i].time-self.start)*self.canvas_width)/duration
						#determine fill
						if tier[i].mark in self.app.Data.getCurrentTraceTracedFrames():
							fill = 'black'
						else:
							fill = 'gray50'
						frame = frames.create_line(x_coord, 0, x_coord, self.canvas_height, tags="frame"+tier[i].mark, fill=fill)
						if first_frame_found == False:
							self.firstFrame = int(tier[i].mark) + 1
							first_frame_found = True
							self.frame_len = tier[i+1].time - tier[i].time
						CanvasTooltip(frames, frame,text=tier[i].mark)
					i+=1
				self.lastFrame = int(tier[i-1].mark)

		self.paintCanvases()
		try:
			self.app.Spectrogram.reset()
			# during startup this gets called before app.Spectrogram is initialized
		except AttributeError:
			pass

	def updateTimeLabels(self):
		'''

		'''
		self.current = self.TextGrid.getFirst(self.frameTierName)[self.app.frame-1].time
		self.TkWidgets[-1]['times'].itemconfig(1,text='{:.6f}'.format(self.start))
		self.TkWidgets[-1]['times'].itemconfig(2,text='{:.6f}'.format(self.end))
		self.TkWidgets[-1]['times'].itemconfig(3,text='{:.6f}'.format(self.current))

	def updateTierLabels(self):
		'''

		'''
		for el in self.TkWidgets:
			if 'canvas' in el:
				current_label = el['canvas-label'].find_all()[0]
				nonempty_frames = el['canvas-label'].gettags(current_label)
				el['canvas-label'].itemconfig(current_label,
				  text='{}:\n({}/{})'.format(el['name'],len(self.getTracedFrames(nonempty_frames)), len(nonempty_frames)))


	def my_find_closest(self, widg, x_loc):
		'''
		replaces TkInter's find_closest function, which is buggy, determines
		whether found item is text, line, or label, and returns corresponding item
		'''
		#could be more efficient FIXME
		maybe_item = None
		dist = 999999999999
		for el in widg.find_all():
			obj_x = widg.coords(el)[0]
			if abs(obj_x-x_loc) < dist:
				dist = abs(obj_x-x_loc)
				maybe_item = el

		if widg in self.tier_pairs.keys(): #on tier-label canvas
			#fill selected tier frames
			# self.setSelectedIntvlFrames(widg,item)
			item = maybe_item

		elif widg in self.tier_pairs.values(): #on canvas with intervals/frames
			if isinstance(maybe_item, int):
				# #if item found is a boundary
				# if len(widg.gettags(maybe_item)) == 0 or widg.gettags(maybe_item) == ('current',):
				if 'line' in widg.gettags(maybe_item):
					#determine on which side of the line the event occurred
					if widg.coords(maybe_item)[0] > x_loc:
						item = maybe_item-1
					else: #i.e. event was on line or to the right of it
						item = maybe_item+1
				else:
					item = maybe_item

				# self.setSelectedIntvlFrames(widg,item)
		else:
			item = maybe_item

		return item
	def setSelectedIntvlFrames(self,tupl):
		''' '''
		widg,item=tupl
		self.selectedIntvlFrames = []
		for x in widg.gettags(item):
			if x[:5] == 'frame':
				self.selectedIntvlFrames.append(x[5:])

	def wipeFill(self):
		'''
		Turns selected frame and interval back to black
		'''
		for frame in range(1,self.app.frames+1):
			if str(frame) in self.app.Data.getCurrentTraceTracedFrames():
				fill = 'black'
			else:
				fill = 'gray50'
			self.frames_canvas.itemconfig('frame'+str(frame), fill=fill)
		if self.selectedItem:
			wdg,itm = self.selectedItem
			# print('line 1381', len(wdg.find_withtag(itm+1)), len(wdg.find_withtag(itm-1)))
			if wdg.type(itm) != 'text' and wdg.type(itm) != None:
				# print(self.selectedItem,self.app.Spectrogram.oldSelected,'line 1374')
				# print(wdg.type(itm),'line 1374')
				wdg,itm = self.app.Spectrogram.oldSelected
			wdg.itemconfig(itm, fill='black')
			if len(wdg.find_withtag(itm+1)) > 0:
				wdg.itemconfig(itm+1, fill='black')
			if len(wdg.find_withtag(itm-1)) > 0:
				wdg.itemconfig(itm-1, fill='black')
			#clicked tier label
			if wdg in self.tier_pairs.keys():
				wdg.itemconfig(1, fill='black')
				self.tier_pairs[wdg].itemconfig(ALL, fill='black')
				self.frames_canvas.itemconfig(ALL, fill='black')

	def genFrameList(self, event=None, widg=None, x_loc=None, SI=False):
		'''
		Upon click, reads frames within interval from the tags to the text item of that interval,
		and highlights text of clicked interval
		'''
		self.wipeFill()
		if event:
			widg=event.widget
			x_loc=event.x

		if SI==False:
			item = self.my_find_closest(widg, x_loc)
			self.selectedItem = (widg, item)
			self.setSelectedIntvlFrames(self.selectedItem)

		#automatically updates frame
		if not str(self.app.frame) in self.selectedIntvlFrames:
			if self.selectedIntvlFrames:
				new_frame = int(self.selectedIntvlFrames[0])
			else:
				frame = self.my_find_closest(self.frames_canvas,x_loc)
				framenum = self.frames_canvas.gettags(frame)[0][5:]
				new_frame = int(framenum)
			if self.firstFrame > new_frame:
				new_frame = self.firstFrame
			elif new_frame > self.lastFrame:
				new_frame = self.lastFrame
			self.app.frame = new_frame
			self.app.framesUpdate()
		else:
			self.paintCanvases()
			self.app.Spectrogram.update()

	def collapse(self, event):
		'''
		collapse or uncollapse selected tier
		'''
		if self.selectedItem != None:
			widg = self.selectedItem[0]
		else:
			widg = event.widget

		if event.num == 1:
			h = self.collapse_height
			if int(widg['height']) == h:
				h = self.canvas_height
		elif event.num == 4 or event.delta > 0:
			h = self.canvas_height
		else:
			h = self.collapse_height

		if int(widg['height']) == h:
			return
		elif h == self.canvas_height:
			mv = (self.canvas_height - self.collapse_height - 14) / 2
		else:
			mv = (self.collapse_height + 14 - self.canvas_height) / 2
		# manually shifting the text by 7 pixels is a rather ugly hack,
		# but it works - DS

		if widg in self.tier_pairs:
				l, c = widg, self.tier_pairs[widg]
		else:
				c = widg
				l = None
				for k in self.tier_pairs:
						if self.tier_pairs[k] == widg:
								l = k
								break
		l.configure(height=h)
		c.configure(height=h)
		l.move('all', 0, mv)
		self.app.event_generate('<Configure>')

	def paintCanvases(self):
		'''

		'''
		if self.selectedItem:
			wdg,itm = self.selectedItem
			#paint selected
			if wdg.type(itm) == 'text':
				wdg.itemconfig(itm, fill='blue')
				#paint boundaries of selected
				if itm+1 in wdg.find_all():
					wdg.itemconfig(itm+1, fill='blue')
				if itm-1 in wdg.find_all():
					wdg.itemconfig(itm-1, fill='blue')
			if wdg in self.tier_pairs.keys(): #if on tier-label canvas
				canvas = self.tier_pairs[wdg]
				for el in canvas.find_all():
					# #make all text intervals blue
					# if canvas.type(canvas.find_withtag(el)) == 'text':
					canvas.itemconfig(el, fill='blue')

			#paint frames
			frames = wdg.gettags(itm)
			# print(frames, wdg, 'line1453')
			for frame in frames:
				if frame[:5] == 'frame':
					frame_obj = self.frames_canvas.find_withtag(frame)
					#detect whether frame contains any traces
					framenum = frame[5:]
					if framenum in self.app.Data.getCurrentTraceTracedFrames():
						fill = 'blue'
					else:
						fill = 'dodger blue'
					self.frames_canvas.itemconfig(frame_obj, fill=fill)

		#current frame highlighted in red
		if self.app.frame:
			self.highlighted_frame = self.frames_canvas.find_withtag('frame'+str(self.app.frame))
			self.frames_canvas.itemconfig(self.highlighted_frame, fill='red')

	def update(self):
		'''

		'''
		# try:
		# 	bloop = self.frames_canvas
		# except AttributeError:
		# 	print("you've been blooped")
		# 	self.reset()

		# print(self.frames_canvas)
		#create list of displayed frames' tags
		itrobj = []
		for itm in self.frames_canvas.find_all():
			itrobj += list(self.frames_canvas.gettags(itm))
		#if selected frame is out of view
		if "frame"+str(self.app.frame) not in itrobj:
			duration = self.end - self.start
			#recenter view on selected frame
			new_time = self.TextGrid.getFirst(self.frameTierName)[self.app.frame-1].time
			self.start = new_time - (duration/2)
			self.end = new_time + (duration/2)
			#redraw
			self.fillCanvases()
		self.wipeFill()
		#if selected frame outside selected interval, select interval on same tier containing frame
		if self.selectedItem:
			if self.selectedItem[0] in self.tier_pairs.keys() or self.selectedItem[0] in self.tier_pairs.values():
				if "frame"+str(self.app.frame) not in self.selectedItem[0].gettags(self.selectedItem[1]): #FIXME should also detect if on label canvas
					widg = self.selectedItem[0]
					if widg in self.tier_pairs:
						widg = self.tier_pairs[widg]
					new_interval = widg.find_withtag("frame"+str(self.app.frame))[0]
					self.selectedItem = (self.selectedItem[0], new_interval)

		# repaint all frames
		self.paintCanvases()
		self.updateTimeLabels()

	def grid(self, event=None):
		'''
		Wrapper for gridding all of our Tk widgets.  This funciton assumes that the tiers (as
		specified in the actual TextGrid files) are in some sort of reasonable order, with the
		default label being drawn on top.
		'''
		for t in range(len(self.TkWidgets)):
			tierWidgets = self.TkWidgets[t]
			if 'label' in tierWidgets:
				tierWidgets['label'].grid(row=t, column=0, sticky=W)
			if 'frames' in tierWidgets:
				tierWidgets['frames'].grid(row=t, column=2, sticky=W, pady=self.app.pady)
				tierWidgets['frames-label'].grid(row=t, column=0, sticky=W, pady=self.app.pady)
			if 'canvas' in tierWidgets:
				tierWidgets['canvas'].grid(row=t, column=2, sticky=W, pady=self.app.pady/2)
				tierWidgets['canvas-label'].grid(row=t, column=0, sticky=W, pady=self.app.pady/2)
				self.tier_pairs[tierWidgets['canvas-label']] = tierWidgets['canvas']
			if 'times' in tierWidgets:
				tierWidgets['times'].grid(row=t, column=2, sticky=S)

	def openSearch(self, event=None):
		self.app.Search.openSearch()

class SpectrogramModule(object):
	def __init__(self,app):
		print( ' - initializing module: Spectrogram' )

		self.app = app

		self.frame = Frame(self.app.BOTTOM)
		self.frame.grid( row=0, column=1, pady=(self.app.pady*2,self.app.pady/2) )
		self.axis_frame = Frame(self.app.BOTTOM)
		self.axis_frame.grid( row=0, column=0, sticky=E, pady=(self.app.pady*2,self.app.pady/2) )
		self.canvas_width = self.app.TextGrid.canvas_width
		self.canvas_height = 106
		self.canvas = Canvas(self.frame, width=self.canvas_width, height=self.canvas_height, background='gray', highlightthickness=0)
		self.spectrogram = None
		self.spec_freq_max = DoubleVar()
		self.wl = DoubleVar()
		self.dyn_range = DoubleVar()
		self.clicktime = -1
		self.specClick = False
		self.oldSelected = None
		self.doDefaults()

		#make spinboxes & buttons for spectrogram specs
		self.spinwin = Frame(self.axis_frame)
		#spinboxes
		axis_ceil_box = Spinbox(self.spinwin, textvariable=self.spec_freq_max, command=self.drawSpectrogram, width=7, increment=100, from_=0, to_=100000)
		axis_ceil_box.bind('<Return>',self.drawSpectrogram)
		axis_ceil_box.bind('<Escape>',lambda ev: self.spinwin.focus())
		wl_box = Spinbox(self.spinwin, textvariable=self.wl, command=self.drawSpectrogram, width=7, increment=0.0005, from_=0, to_=1)
		wl_box.bind('<Return>',self.drawSpectrogram)
		wl_box.bind('<Escape>',lambda ev: self.spinwin.focus())
		dyn_range_box = Spinbox(self.spinwin, textvariable=self.dyn_range, command=self.drawSpectrogram, width=7, increment=10, from_=0, to_=10000)
		dyn_range_box.bind('<Return>',self.drawSpectrogram)
		dyn_range_box.bind('<Escape>',lambda ev: self.spinwin.focus())
		#buttons
		default_btn = Button(self.spinwin, text='Standards', command=self.restoreDefaults, takefocus=0)
		apply_btn = Button(self.spinwin, text='Apply', command=self.drawSpectrogram, takefocus=0)

		# self.axis_frame.create_window(wwidth,self.canvas_height, window=self.spinwin, anchor=NE)
		#grid spinboxes & buttons on subframe
		axis_ceil_box.grid(row=0, columnspan=2, sticky=NE)
		wl_box.grid(row=1, columnspan=2, sticky=NE)
		dyn_range_box.grid(row=2, columnspan=2, sticky=NE)
		default_btn.grid(row=3)
		apply_btn.grid(row=3, column=1)

		self.grid()

		self.canvas.bind('<Button-1>', self.jumpToFrame)
		# self.canvas.bind('<Shift-Button-1>', self.jumpToFrame)

	def doDefaults(self):
		self.spec_freq_max.set(5000.0)
		self.wl.set(0.005)
		self.dyn_range.set(90)

	def restoreDefaults(self):
		self.doDefaults()
		self.drawSpectrogram()

	def update(self):
		'''
		Removes and redraws lines on top of Spectrogram corresponding to selected interval(s)
		'''
		self.canvas.delete('line')
		self.drawInterval()

	def reset(self):
		self.drawSpectrogram()
		self.drawInterval()

	def drawSpectrogram(self, event=None):
		'''
		Extracts spectrogram data from sound, and draws it to canvas
		'''
		if self.app.Audio.current:
			sound = parselmouth.Sound(self.app.Audio.current)

			ts_fac = decimal.Decimal(10000.0)
			wl = decimal.Decimal(self.wl.get())
			start_time = self.app.TextGrid.start
			end_time = decimal.Decimal(self.app.TextGrid.end)

			# the spectrogram is for the audio file, so it makes sense
			# to get the duration from the audio file and not from the
			# textgrid -JNW
			duration = end_time - start_time
			#duration = decimal.Decimal(sound.get_total_duration())
			# in case there isn't a TextGrid or there's some other issue: -JNW
			if start_time == end_time:
				end_time = decimal.Decimal(sound.get_total_duration())

			self.ts = duration / ts_fac
			# the amount taken off in spectrogram creation seems to be
			# ( 2 * ts * floor( wl / ts ) ) + ( duration % ts )
			# but we've defined ts as duration / 10000, so duration % ts = 0
			# so the amount to increase the length by is ts * floor( wl / ts )
			# at either end - D.S.
			extra = self.ts * math.floor( wl / self.ts )
			start_time = max(0, start_time - extra)
			end_time = min(end_time + extra, sound.get_total_duration())
			sound_clip = sound.extract_part(from_time=start_time, to_time=end_time)

			spec = sound_clip.to_spectrogram(window_length=wl, time_step=self.ts, maximum_frequency=self.spec_freq_max.get())
			self.spectrogram = 10 * np.log10(np.flip(spec.values, 0))

			# self.spectrogram += self.spectrogram.min()
			# self.spectrogram *= (60.0 / self.spectrogram.max())

			mx = self.spectrogram.max()
			dyn = self.dyn_range.get()
			# print(self.spectrogram.min(), self.spectrogram.max())
			self.spectrogram = self.spectrogram.clip(mx-dyn, mx) - mx
			# print(self.spectrogram.min(), self.spectrogram.max())
			self.spectrogram *= (-255.0 / dyn)
			# self.spectrogram += 60
			# print(self.spectrogram.min(), self.spectrogram.max())

			img = Image.fromarray(self.spectrogram)
			if img.mode != 'RGB':
				img = img.convert('RGB')
			# contrast = ImageEnhance.Contrast(img)
			# img = contrast.enhance(5)
			# self.canvas_height = img.height
			img = img.resize((self.canvas_width, self.canvas_height))

			photo_img = ImageTk.PhotoImage(img)
			self.canvas.config(height=self.canvas_height)

			# self.canvas.create_image(0,0, anchor=NW, image=photo_img)
			# self.canvas.create_image(self.canvas_width/2,self.canvas_height/2, image=photo_img)
			if self.app.TextGrid.selectedItem:
				tags = self.app.TextGrid.selectedItem[0].gettags(self.app.TextGrid.selectedItem[1])
			self.canvas.delete(ALL)
			img = self.canvas.create_image(self.canvas_width, self.canvas_height, anchor=SE, image=photo_img)
			self.img = photo_img
			#pass on selected-ness
			if self.app.TextGrid.selectedItem:
				if self.app.TextGrid.selectedItem[0] == self.canvas:
					self.app.TextGrid.selectedItem = (self.canvas, img)
					#pass on tags
					for tag in tags:
						self.canvas.addtag_all(tag)

	def drawInterval(self):
		'''
		Adapted with permission from
		https://courses.engr.illinois.edu/ece590sip/sp2018/spectrograms1_wideband_narrowband.html
		by Mark Hasegawa-Johnson
		'''
		if self.app.TextGrid.selectedItem:
			widg = self.app.TextGrid.selectedItem[0]
			itm = self.app.TextGrid.selectedItem[1]

			if widg in self.app.TextGrid.tier_pairs: #if widg is label
				itvl_canvas = self.app.TextGrid.tier_pairs[widg]
				for i in itvl_canvas.find_withtag('line'):
					loc = itvl_canvas.coords(i)[0]
					self.canvas.create_line(loc, 0, loc, self.canvas_height, tags='line', fill='blue')
			elif widg in self.app.TextGrid.tier_pairs.values(): #if widg is textgrid canvas
				if itm-1 in widg.find_all():
					l_loc = widg.coords(itm-1)[0]
					self.canvas.create_line(l_loc, 0, l_loc, self.canvas_height, tags='line', fill='blue')
				if itm+1 in widg.find_all():
					r_loc = widg.coords(itm+1)[0]
					self.canvas.create_line(r_loc, 0, r_loc, self.canvas_height, tags='line', fill='blue')
			elif widg == self.canvas:
				l_time, r_time = self.app.TextGrid.getMinMaxTime()
				l_loc = self.timeToX(float(l_time))
				r_loc = self.timeToX(float(r_time))
				self.canvas.create_line(l_loc, 0, l_loc, self.canvas_height, tags='line', fill='blue')
				self.canvas.create_line(r_loc, 0, r_loc, self.canvas_height, tags='line', fill='blue')

			#draw selected frame
			if self.app.TextGrid.firstFrame <= self.app.frame <= self.app.TextGrid.lastFrame :
				xcoord = self.app.TextGrid.frames_canvas.coords(self.app.TextGrid.highlighted_frame)[0]
				self.canvas.create_line(xcoord,0,xcoord,self.canvas_height, tags='line', fill='red')
			#draw line where user last clicked on spectrogram
			if self.clicktime != -1 and self.specClick == False:
				x = self.timeToX(self.clicktime)
				self.canvas.create_line(x,0,x,self.canvas_height, tags='line', fill='green')

	def jumpToFrame(self, event):
		'''  '''
		#restore textgrid selected interval between clicks
		if not self.app.TextGrid.selectedItem:
			key = next(iter(self.app.TextGrid.tier_pairs))
			wdg = self.app.TextGrid.tier_pairs[key]
			self.app.TextGrid.selectedItem = (wdg,wdg.find_all()[0])
			self.app.TextGrid.setSelectedIntvlFrames(self.app.TextGrid.selectedItem)
		if self.app.TextGrid.selectedItem[0] == self.canvas:
			self.app.TextGrid.selectedItem = self.oldSelected
			self.app.TextGrid.setSelectedIntvlFrames(self.app.TextGrid.selectedItem)
		#prevents wiping of canvases because of mouse click
		# self.app.resized = False
		# draw line at click location
		x = self.canvas.canvasx(event.x)
		self.clicktime = self.xToTime(x)
		#jump to new frame
		frame = self.app.TextGrid.my_find_closest(self.app.TextGrid.frames_canvas, self.canvas.canvasx(event.x))
		framenum = self.app.TextGrid.frames_canvas.gettags(frame)[0][5:]
		self.app.frame=int(framenum)
		self.app.framesUpdate()
		#remember which interval was selected before specgram click
		if event.state==1:
			self.oldSelected = self.app.TextGrid.selectedItem
		#for selecting & zooming interval (w/ shift)
			self.specClick = True

	def xToTime(self, x):
		''' converts from a x coordinate (relative to the canvas) to the timestamp at that coordinate'''
		return (x*float(self.app.TextGrid.end - self.app.TextGrid.start)/self.canvas_width) + float(self.app.TextGrid.start)
	def timeToX(self,time):
		''' converts from a time to the x coordinate on a canvas representing that time'''
		return self.canvas_width*(time - float(self.app.TextGrid.start))/float(self.app.TextGrid.end - self.app.TextGrid.start)

	def grid(self):
		'''
		Put tkinter items on app
		'''
		self.canvas.grid(row=0, column=0, sticky=N+S+E+W)
		self.spinwin.grid(row=0,column=0,sticky=NE)
		# self.axis_canvas.grid(row=0,column=0,sticky=SE)


class TraceModule(object):
	'''
	Module to manage all of the different traces (with unique names/colors) and the
	Crosshairs objects associated to each one.  In particular, handles creation/modfication
	of traces and crosshairs.
	'''
	def __init__(self, app):
		print( ' - initializing module: Trace' )

		self.app = app

		# some images for the buttons
		# Source for icons: https://material.io/tools/icons/?style=outline
		# License: Apache Version 2.0 www.apache.org/licenses/LICENSE-2.0.txt
		data_copy = '''R0lGODlhGAAYAPAAAAAAAAAAACH5BAEAAAEALAAAAAAYABgAAAJHjI+pCe3/1oHUSdOunmDvHFTWBYrjUnbMuWIqAqEqCMdt+HI25yrVTZMEcT3NMPXJEZckJdKorCWbU2H0JqvKTBErl+XZFAAAOw'''
		data_paste = '''R0lGODlhGAAYAPAAAAAAAAAAACH5BAEAAAEALAAAAAAYABgAAAJBjI+pq+DAonlPToqza7rv9FlBeJCSOUJpd3EXm7piDKoi+nkqvnttPaMhUAzeiwJMapJDm8U44+kynCkmiM1qZwUAOw'''

		self.img_copy = PhotoImage(data=data_copy)
		self.img_paste = PhotoImage(data=data_paste)

		self.displayedColour = None
		#self.app.Data.getCurrentTraceColor()

		# array of trace names for this directory
		self.available = self.app.Data.getTopLevel( 'traces' )
		self.available = [] if self.available==None else self.available

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
		self.listbox = Listbox(lbframe, yscrollcommand=self.scrollbar.set, width=12, exportselection=False)
		self.scrollbar.config(command=self.listbox.yview)
		for trace in self.available:
			self.listbox.insert(END, trace)
		for i, item in enumerate(self.listbox.get(0, END)):
			# select our "default trace"
			if item==self.app.Data.getTopLevel( 'defaultTraceName' ):
				self.listbox.selection_clear(0, END)
				self.listbox.select_set( i )

		# this module is responsible for so many widgets that we need a different
		# strategy for keeping track of everything that needs constistent grid() /
		# grid_remove() behavior
		self.TkWidgets = [
			self.getWidget( Header(self.frame, text="Choose a trace"), row=5, column=0, columnspan=4 ),
			self.getWidget( lbframe, row=10, column=0, rowspan=50 ),
			self.getWidget( Button(self.frame, text='Set as default', command=self.setDefaultTraceName, takefocus=0), row=10, column=2, columnspan=2 ),
			self.getWidget( Button(self.frame, text='Select all', command=self.selectAll, takefocus=0), row=11, column=2, columnspan=2 ),
			self.getWidget( Button(self.frame, image=self.img_copy, command=self.copy, takefocus=0), row=12, column=2 ), # FIXME: add tooltip for "Copy"
			self.getWidget( Button(self.frame, image=self.img_paste, command=self.paste, takefocus=0), row=12, column=3 ), # FIXME: add tooltip for "Paste"
			self.getWidget( Entry( self.frame, width=8, textvariable=self.displayedColour), row=13, column=1, columnspan=2, sticky=W ),
			self.getWidget( Button(self.frame, text='Recolor', command=self.recolor, takefocus=0), row=13, column=3 ),
			self.getWidget( Button(self.frame, text='Clear', command=self.clear, takefocus=0), row=15, column=2, columnspan=2 ),
			self.getWidget( Entry( self.frame, width=12, textvariable=self.traceSV), row=100, column=0, sticky=W ),
			self.getWidget( Button(self.frame, text='New', command=self.newTrace, takefocus=0), row=100, column=2 ),
			self.getWidget( Button(self.frame, text='Rename', command=self.renameTrace, takefocus=0), row=100, column=3 ) ]

		# there's probably a better way to do this than indexing into self.TkWidgets
		self.TkWidgets[6]['widget'].bind('<Return>', lambda ev: self.TkWidgets[0]['widget'].focus())
		self.TkWidgets[6]['widget'].bind('<Escape>', lambda ev: self.TkWidgets[0]['widget'].focus())
		self.TkWidgets[9]['widget'].bind('<Return>', lambda ev: self.TkWidgets[0]['widget'].focus())
		self.TkWidgets[9]['widget'].bind('<Escape>', lambda ev: self.TkWidgets[0]['widget'].focus())

		if _PLATFORM == 'Linux':
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
		#print("TraceModule", self.frame.winfo_width())
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
		except:# _tkinter.TclError:
			print( 'Can\'t select from empty listbox!' )
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
		within a globally defined _CROSSHAIR_SELECT_RADIUS

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
					for i, item in enumerate(self.listbox.get(0, END)):
						if item==trace:
							self.listbox.selection_clear(0, END)
							self.listbox.select_set( i )
					return nearby

		return None
	def getNearClickOneTrace(self, click, trace):
		'''
		takes a click object and a trace and returns a list of crosshairs within
		_CROSSHAIR_SELECT_RADIUS of that click
		'''

		# see if we clicked near any existing crosshairs
		possibleSelections = {}
		if trace in self.crosshairs:
			for ch in self.crosshairs[ trace ]:
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

		return None

	def copy(self, event=None):
		''' copies relative positions of selected crosshairs for pasting'''
		# print('copy')
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
			self.listbox.insert(END, name)
			self.listbox.selection_clear(0, END)
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
			self.listbox.selection_clear(0, END)
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
			'row'	 : row,
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
		self.listbox.pack(side=LEFT, fill=Y)
		self.scrollbar.pack(side=RIGHT, fill=Y)
	def grid_remove(self):
		''' remove all of our widgets from the grid '''
		for item in self.TkWidgets:
			item['widget'].grid_remove()
		self.listbox.packforget()
		self.scrollbar.packforget()

class PlaybackModule(object):
	'''
	Module to handle playback of audio and video files.
	'''
	def __init__(self, app):
		self.app = app
		self.current = None
		if _AUDIO_LIBS_INSTALLED:
			print( ' - initializing module: Audio' )
			self.sfile = None
			self.p = pyaudio.PyAudio()
			self.currentInterval = None
			self.started = False
			self.paused = False
			self.sync = threading.Event()
			self.stoprequest = threading.Event()

			# widget management
			self.frame = Frame(self.app.BOTTOM)
			self.playBtn = Button(self.frame, text="Play/Pause", command=self.playpauseAV, state=DISABLED, takefocus=0) # NOTE: not currently appearing
			self.app.bind('<space>', self.playpauseAV )
			self.app.bind('<Escape>', self.stopAV )
		if _VIDEO_LIBS_INSTALLED:
			print( ' - initializing module: Video' )
			self.app.bind('<space>', self.playpauseAV )
			self.app.bind('<Escape>', self.stopAV )
		self.reset()

	def update(self):
		'''
		don't change the audio file when we change frames
		'''
		pass

	def reset(self):
		'''
		try to load an audio file
		'''
		if _AUDIO_LIBS_INSTALLED:
			self.current = None
			audioFallbacks = [ '.wav', '.flac', '.ogg', '.mp3' ]
			for codec in audioFallbacks:
				if self.loadAudio( codec ) == True:
					self.playBtn.config( state=NORMAL )
					return

	def loadAudio(self, codec):
		'''
		load an audio file with a specific codec
		'''
		audiofile = self.app.Data.getFileLevel( codec )
		if audiofile != None:
			try:
				audiofile = self.app.Data.unrelativize(audiofile)
				self.sfile = AudioSegment.from_file( audiofile )
				self.current = audiofile
				self.duration = len(self.sfile)/1000.0
				return True
			except:
				print('Unable to load audio file: `%s`' % audiofile)
				return False

	def playpauseAV(self, event):
		'''

		'''
		# print(self.started, self.paused, '1858')
		if self.started == False or self.currentInterval != self.app.TextGrid.selectedItem: #if we haven't started playing or we're in a new interval
			#reset monitoring variables
			self.currentInterval = self.app.TextGrid.selectedItem
			self.started = False
			self.paused = False

			if self.app.TextGrid.selectedItem:
				start, end = self.app.TextGrid.getMinMaxTime()
			else:
				start = self.app.TextGrid.start
				end = self.app.TextGrid.end

			# if _VIDEO_LIBS_INSTALLED and _AUDIO_LIBS_INSTALLED:
			# 	self.readyVideo()
			# 	self.readyAudio(start, end)
			# 	self.playAudio()
			# elif _AUDIO_LIBS_INSTALLED:
			# 	self.readyAudio(start, end)
			# 	self.playAudio()
			# elif _VIDEO_LIBS_INSTALLED:
			# 	self.readyVideo()
			# 	self.dicomframeQ = queue.Queue()
			# 	for i in range(len(self.pngs)):
			# 		self.dicomframeQ.put(self.pngs[i])
			# 	self.playVideoNoAudio()

			if self.app.Dicom.isLoaded:
				self.readyVideo()
			if _AUDIO_LIBS_INSTALLED:
				self.readyAudio(start, end)
				self.playAudio()
			elif self.app.Dicom.isLoaded:
				self.dicomframeQ = queue.Queue()
				for i in range(len(self.pngs)):
					self.dicomframeQ.put(self.pngs[i])
				self.playVideoNoAudio()

		elif self.started == True:
			if self.paused == False:
				self.paused = True
				self.stream.stop_stream()
			else:
				self.paused = False
				self.playAudio()

	def readyAudio(self, start, end):
		'''

		'''
		#audio stuff
		start_idx = round(float(start)*1000)
		end_idx = round(float(end)*1000)
		self.flen = float(self.app.TextGrid.frame_len)
		fpb = 512
		extrafs = (end_idx-start_idx)%fpb
		extrasecs = extrafs/self.sfile.frame_rate
		pad = AudioSegment.silent(duration=round(extrasecs*1000))
		seg_nopad = self.sfile[start_idx:end_idx]
		self.seg = seg_nopad + pad
		# seg.append()
		self.audioframe = 0

		# open stream using callback (3)
		self.stream = self.p.open(format=self.p.get_format_from_width(self.seg.sample_width),
		                channels=self.seg.channels,
		                rate=self.seg.frame_rate,
						frames_per_buffer=fpb,
		                output=True,
						start=False,
		                stream_callback=self.callback)

		# print(self.seg.frame_count()/fpb, 'number of chunks')
		# print(self.seg.frame_count()%fpb, 'last chunk size')
		# self.chunkcount = 0

	def readyVideo(self):
		'''

		'''
		tags = self.app.TextGrid.selectedItem[0].gettags(self.app.TextGrid.selectedItem[1])
		framenums = [tag[5:] for tag in tags if tag[:5]=='frame']
		self.framestart = int(framenums[0])
		png_locs = [self.app.Data.getPreprocessedDicom(frame) for frame in framenums]
		canvas = self.app.Dicom.zframe.canvas
		bbox = canvas.bbox(canvas.find_all()[0])
		dim = (bbox[2] - bbox[0], bbox[3] - bbox[1])
		imgs = [Image.open(png).resize(dim) for png in png_locs]
		self.pngs = []
		traces = self.app.Data.getTopLevel('traces')
		file = self.app.Data.getCurrentFilename()
		l = _CROSSHAIR_SELECT_RADIUS
		for frame, img in zip(framenums, imgs):
			draw = ImageDraw.Draw(img)
			for name in traces:
				color = traces[name]['color']
				if file in traces[name]['files'] and frame in traces[name]['files'][file]:
					for pt in traces[name]['files'][file][frame]:
						x = int(pt['x'] * img.width)
						y = int(pt['y'] * img.height)
						draw.line((x-l, y, x+l, y), fill=color)
						draw.line((x, y-l, x, y+l), fill=color)
			del draw
			self.pngs.append(ImageTk.PhotoImage(img))

		#video w/audio stuff
		self.dicomframe_timer = 0
		self.dicomframe_num = 1
		self.dicomframeQ = queue.Queue()
		self.dicomframeQ.put(self.pngs[0]) #put now, because audio callback puts frames when audio segments end
		# for i in range(len(self.pngs)):
		# 	self.dicomframeQ.put(self.pngs[i])

	def callback(self, in_data, frame_count, time_info, status):
		'''
		Called by pyaudio stream. Gets chunks of audio ready for playing
		With video capabilities, also updates video frame information
		'''
		# self.sync.clear()
		# self.chunkcount+=1
		data = b''.join([self.seg.get_frame(i) for i in range(self.audioframe, self.audioframe+frame_count)])
		# print(len(data), 'line 1960')
		self.audioframe+=frame_count

		if self.app.Dicom.isLoaded:
			#check & update video frame
			canvas = self.app.Dicom.zframe.canvas
			callbacklen = frame_count/self.seg.frame_rate
			self.dicomframe_timer += callbacklen
			#go to next frame
			if self.dicomframe_timer % self.flen != self.dicomframe_timer and self.dicomframe_num < len(self.pngs):
				floor = math.floor(self.dicomframe_timer/self.flen)
				# print(floor, 'line 1961')
				self.dicomframe_timer = self.dicomframe_timer-self.flen*floor
				if floor > 1:
					for i in range(floor-1):
						# print(self.dicomframe_num+self.framestart+i, 'putting frame into Q')
						if self.dicomframe_num+i < len(self.pngs):
							self.dicomframeQ.put(self.pngs[self.dicomframe_num+i])
				else:
					self.dicomframeQ.put(self.pngs[self.dicomframe_num])
				# self.sync.set()
				self.dicomframe_num+=floor

				# print(self.dicomframe_num, len(self.pngs), 'line 1968')
			# else: #stop video loop
				if self.dicomframe_num >= len(self.pngs):
					self.stoprequest.set()

		return (data, pyaudio.paContinue)

	def playAudio(self):
		self.stream.start_stream()
		self.started = True
		if self.app.Dicom.isLoaded:
			self.playVideoWithAudio()
		else:
			pass #write a loop that keeps audio playing
		# stop stream (6)
		if self.stoprequest.is_set():
			self.stopAV()
		# self.stream.stop_stream()
		# if self.stoprequest.is_set():
		# 	self.stream.close()
		# 	self.started = False
		# print(self.chunkcount)
		# close PyAudio (7)
		# self.p.terminate() # NOTE: needs to be removed in order to play multiple audio files in a row

	def playVideoWithAudio(self):
		'''

		'''
		# self.sync.wait()
		if self.paused == True:
			return
		canvas = self.app.Dicom.zframe.canvas
		# print(self.dicomframeQ.qsize(),'line 1991')
		try:
			pic = self.dicomframeQ.get(timeout=.5)
			canvas.itemconfig(canvas.find_all()[0] , image=pic )
			# canvas.lift(pic)
			# canvas.img = pic
			canvas.update()
		except: pass
		# print(pic, 'displayed')
		# print(self.dicomframe_num+self.framestart, 'displayed')
		if not self.stoprequest.is_set() or not self.dicomframeQ.empty(): #should this if be at the top?
			self.playVideoWithAudio()
			# canvas.after(10, self.playVideoWithAudio)

	def playVideoNoAudio(self):
		'''

		'''
		canvas = self.app.Dicom.zframe.canvas
		# pic = self.dicomframeQ.get()
		pic = self.dicomframeQ.get(block=False)
		canvas.itemconfig( canvas.find_all()[0], image=pic )
		canvas.update()
		if not self.dicomframeQ.empty() and self.stoprequest.is_set() == False: #should this if be at the top?
			self.playVideoNoAudio()

	def stopAV(self,event=None):
		self.stoprequest.set()
		if _AUDIO_LIBS_INSTALLED:
			self.stream.stop_stream()
			self.stream.close()
		self.started = False
		self.paused = False
		self.app.framesJumpTo()
		self.stoprequest.clear()

	def grid(self):
		''' grid widgets '''
		self.frame.grid( row=0 )
		self.playBtn.grid()

	def ungrid(self):
		''' remove widgets from grid '''
		self.frame.grid_remove()
		self.playBtn.grid_remove()

class DicomModule(object):
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
		print( ' - initializing module: Dicom')

		self.app = app
		self.isLoaded = False

		if _DICOM_LIBS_INSTALLED:
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
			if _PLATFORM == 'Linux':
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
			image = Image.open( image )
			self.zframe.setImage( image )

	def load(self, event=None):
		'''
		brings a dicom file into memory if it exists
		'''
		if _DICOM_LIBS_INSTALLED:
			# don't execute if dicom already loaded correctly
			if self.isLoaded == False:

				processed = self.app.Data.getFileLevel( 'processed' )
				# print(os.path.exists(self.app.Data.unrelativize(self.app.Data.getFileLevel( 'processed' )['1'])))
				if processed == None:
					return self.process()
				# elif :
				# 	self.process()
				# else:
				# 	self.app.frames = len(processed)

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
		print( 'Reading DICOM data ...', end='\r' )

		if self.isLoaded == False:
			try:
				dicomfile = self.app.Data.getFileLevel( '.dicom' )
				self.dicom = dicom.read_file( self.app.Data.unrelativize(dicomfile) )

			except dicom.errors.InvalidDicomError:
				print( 'Unable to read DICOM file: %s' % dicomfile )
				return False

		pixels = self.dicom.pixel_array # np.array
		self.frametime = self.dicom.get('FrameTime')
		self.numframes = self.dicom.get('NumberOfFrames')
		self.app.Data.setFileLevel('FrameTime', self.frametime)
		self.app.Data.setFileLevel('NumberOfFrames', self.numframes)

		# check encoding, manipulate array if we need to
		if len(pixels.shape) == 3:		# greyscale
			RGB = False
			frames, rows, columns = pixels.shape
		elif len(pixels.shape) == 4:	# RGB-encoded
			RGB = True
			if pixels.shape[0] == 3:	# handle RGB-first
				rgb, frames, rows, columns = pixels.shape
			else:						# and RGB-last
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
		# print(self.app.Data.getFileLevel('name'))
		# print()
		# grab one frame at a time to write (and provide a progress indicator)
		printProgressBar(0, frames, prefix = 'Processing:', suffix = 'complete')
		for f in range( frames ):

			printProgressBar(f+1, frames, prefix = 'Processing:', suffix = ('complete (%d of %d)' % (f+1,frames)))

			arr = pixels[ f,:,:,: ] if RGB else pixels[ f,:,: ]
			img = Image.fromarray( arr )

			outputfilename = '%s_frame_%04d.png' % ( os.path.basename(self.app.Data.getFileLevel('name')), f+1 )
			outputfilepath = os.path.join( rel_outputpath, outputfilename )
			# print(outputpath, outputfilename,'line 2457')
			# print(outputfilepath)
			img.save( os.path.join(self.app.Data.path,outputfilepath), format='PNG', compress_level=1 )

			# keep track of all the processing we've finished
			# print(os.path.join(outputpath,outputfilename))
			processedData[ str(f+1) ] = outputfilepath
		# print(processedData)
		self.app.Data.setFileLevel( 'processed', processedData )
		self.app.lift()
		self.load()
		self.app.update()
		self.app.framesUpdate()

	# an attempt at making things parallel, but we get the following error:
	# _pickle.PicklingError: Could not pickle the task to send it to the workers.

	# 	#for f in range(frames):
	# 	Parallel(n_jobs=2)(delayed(self.writeTempImage)(f, frames, outputpath, RGB, pixels) for f in range(frames))
	#
	#
	# 	self.app.Data.setFileLevel( 'processed', self.processedData )
	# 	self.app.lift()
	# 	self.load()
	#
	# def writeTempImage(self, f, frames, outputpath, RGB, pixels):
	#
	# 	#printProgressBar(f+1, frames, prefix = 'Processing:', suffix = ('complete (%d of %d)' % (f+1,frames)))
	#
	# 	arr = pixels[ f,:,:,: ] if RGB else pixels[ f,:,: ]
	# 	img = Image.fromarray( arr )
	#
	# 	outputfilename = '%s_frame_%04d.png' % ( self.app.Data.getFileLevel('name'), f )
	# 	outputfilepath = os.path.join( outputpath, outputfilename )
	# 	img.save( outputfilepath, format='PNG' )
	#
	# 	## keep track of all the processing we've finished
	# 	#self.processedData[ str(f) ] = outputfilepath
	# 	return (str(f), outputfilepath)

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
		self.app.framesHeader.grid(	  row=0 )
		self.app.framesPrevBtn.grid(	  row=0, column=0 )
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
		print( ' - initializing module: Control' )
		# reference to our main object containing other functionality managers
		self.app = app
		# initialize our stacks
		self.reset()
		# bind Ctrl+z to UNDO and Ctrl+Shift+Z to REDO
		if _PLATFORM == 'Linux':
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
				print (item)
				raise NotImplementedError

			self.app.Trace.unselectAll()
			self.app.Trace.write()
			self.updateButtons()
		else:
			print( 'Nothing to undo!' )
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
				print (item)
				raise NotImplementedError

			self.app.Trace.unselectAll()
			self.app.Trace.write()
			self.updateButtons()
		else:
			print( 'Nothing to redo!' )
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
		#self.input.bind('<Enter>', self.search)
		self.searchButton = Button(self.window, text='Search', command=self.search)
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
				grid = TextGrid.fromFile(self.app.Data.unrelativize(tg))
				for tier in grid:
					if isinstance(tier, IntervalTier):
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

		print()
		print( 'initializing UltraTrace' )

		# do the normal Tk init stuff
		if _PLATFORM=='Linux':
			try:
				Xresources = xrp.parse_file(os.path.join(str(Path.home()), '.Xresources'))
				if '*TtkTheme' in Xresources.resources:
					ttktheme = Xresources.resources['*TtkTheme']
					print("Setting Linux Ttk theme to {}".format(ttktheme))
				elif '*TkTheme' in Xresources.resources:
					ttktheme = Xresources.resources['*TkTheme']
					print("Setting Linux Tk theme to {}".format(ttktheme))
				else:
					ttktheme = "clam"  # alt, clam, classic, default
					print("Falling back to default Linux Tk theme: {}".format(ttktheme))
				super().__init__(theme=ttktheme)
			except Exception as e:
				print("exception: ", e)
				super().__init__()
		else:
			super().__init__()
		self.title('UltraTrace')

		# check if we were passed a command line argument
		parser = argparse.ArgumentParser()
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

		print( ' - loading widgets' )

		self.filesUpdate()
		# self.framesUpdate()
		# self.TextGrid.startup() #NOTE why does TextGridModule have to reset a second time? Is there a more economical way to do this?

		print()

		# to deal with resize handler being called multiple times
		# in a single window resize
		self.isResizing = False

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
				# print(canvas.gettags(ALL))
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
			image = Image.open( png_loc )
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
				if dx > _CROSSHAIR_DRAG_BUFFER or dy > _CROSSHAIR_DRAG_BUFFER:
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
			print( 'Please enter an integer!' )

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
		print( 'App encountered a UnicodeDecodeError when attempting to bind a \
<MouseWheel> event.  This is a known bug with Tcl/Tk 8.5 and can be fixed by \
changing a file in the Tkinter module in the python3 std libraries.  To make this \
change, copy the file `tkinter__init__.py` from this directory to the library for \
your standard system installation of python3.  For example, your command might \
look like this:\n\n\t$ cp ./tkinter__init__.py /Library/Frameworks/Python.\
frameworks/Versions/3.6/lib/python3.6/tkinter/__init__.py\n \
or\t$ cp ./tkinter__init__.py /usr/local/Frameworks/Python.framework/Versions/3.\
6/lib/python3.6/tkinter/__init__.py\nDepending on your python deployment.' )
