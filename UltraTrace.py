#!/usr/bin/env python3

# core libs
from tkinter import *
from tkinter import filedialog
import argparse, datetime, json, \
	math, os, random, shutil, warnings

# monkeypatch the warnings module
warnings.showwarning = lambda msg, *args : print( 'WARNING: %s' % msg )

# critical dependencies
from magic import Magic # sudo -H pip3 install -U python-magic
getMIMEType = Magic(mime=True).from_file

# non-critical dependencies
try:
	import numpy as np				# sudo -H pip3 install -U numpy
	import pydicom as dicom 		# sudo -H pip3 install -U pydicom
	from PIL import Image, ImageTk  # sudo -H pip3 install -U pillow
	_DICOM_LIBS_INSTALLED = True
except (ImportError):
	warnings.warn('Dicom library failed to load')
	_DICOM_LIBS_INSTALLED = False
try:
	import pygame 	# sudo -H pip3 install pygame pygame.mixer && brew install sdl sdl_mixer
	assert("pygame.mixer" in sys.modules)
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
	from textgrid import TextGrid, IntervalTier, PointTier # sudo -H pip3 install -U textgrid
	_TEXTGRID_LIBS_INSTALLED = True
except (ImportError):
	warnings.warn('TextGrid library failed to load')
	_TEXTGRID_LIBS_INSTALLED = False

# some globals
_CROSSHAIR_DRAG_BUFFER = 20
_CROSSHAIR_SELECT_RADIUS = 12
_TEXTGRID_ALIGNMENT_TIER_NAMES = [ 'frames', 'all frames', 'dicom frames', 'ultrasound frames' ]

class ZoomFrame(Frame):
	'''
	Wrapper for a Tk Frame() object that includes zooming and panning functionality.
	This code is inspired by the answer from https://stackoverflow.com/users/7550928/foo-bar
	at https://stackoverflow.com/questions/41656176/tkinter-canvas-zoom-move-pan ...
	Could probably be cleaned up and slimmed down
	'''
	def __init__(self, master, delta, ):
		Frame.__init__(self, master)
		self.resetCanvas(master)

		self.delta = delta
		self.maxZoom = 5

	def resetCanvas(self, master):

		self.canvas = Canvas( master,  bg='grey', width=800, height=600 )
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

		self.zoom = 0
		self.imgscale = 1.0
		self.image = None

	def setImage(self, image): # expect an Image() instance
		self.zoom = 0
		self.imgscale = 1.0
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

	def wheel(self, event):
		if self.image != None:
			x = self.canvas.canvasx(event.x)
			y = self.canvas.canvasy(event.y)
			scale = 1.0

			# Respond to Linux (event.num) or Windows (event.delta) wheel event
			if event.num == 5 or event.delta < 0:  # zoom in
				if self.zoom < self.maxZoom:
					self.zoom += 1
					self.imgscale /= self.delta
					scale         /= self.delta
					self.canvas.scale('all', x, y, scale, scale)  # rescale all canvas objects

			if event.num == 4 or event.delta > 0:  # zoom out
				if self.zoom > self.maxZoom * -1:
					self.zoom -= 1
					self.imgscale *= self.delta
					scale         *= self.delta
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

class Header(Label):
	def __init__(self, master, text):
		'''
		Wrapper for Tk Label() object with a specified font
		'''
		Label.__init__(self, master, text=text, font='TkDefaultFont 12 bold')

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
		self.selectedWidth  = 3
		self.unselectedWidth= 2
		self.defaultLength  = 12

		# store position data
		self.x, self.y = x, y
		if transform:
			self.x, self.y = self.transformCoords(x,y)
		self.len = self.transformLength( self.defaultLength )
		self.resetTrueCoords()
		self.isSelected = False
		self.isVisible = True

		# draw on the canvas
		self.hline = self.zframe.canvas.create_line(self.x-self.len, self.y, self.x+self.len, self.y, fill=self.unselectedColor, width=self.unselectedWidth)
		self.vline = self.zframe.canvas.create_line(self.x, self.y-self.len, self.x, self.y+self.len, fill=self.unselectedColor, width=self.unselectedWidth)

	def resetTrueCoords(self):
		'''
		This function calculates the `true` coordinates for saving our crosshairs to the metadata file.
		The values are calculated relative to the top left corner of the canvas at 1x zoom.  We need to
		make sure to call this every time we change the position of a Crosshairs.
		'''
		self.trueX, self.trueY = self.transformCoordsToTrue(self.x,self.y)

	def getTrueCoords(self):
		''' called when we're saving to file '''
		return self.trueX, self.trueY

	def transformCoordsToTrue(self, x, y):
		''' canvas coords -> absolute coords '''
		containerX, containerY = self.zframe.canvas.coords( self.zframe.container )[:2]
		x = (x-containerX) / self.zframe.imgscale
		y = (y-containerY) / self.zframe.imgscale
		return x, y

	def transformTrueToCoords(self, x, y):
		''' absolute coords -> canvas coords '''
		containerX, containerY = self.zframe.canvas.coords( self.zframe.container )[:2]
		x = x*self.zframe.imgscale + containerX
		y = y*self.zframe.imgscale + containerY
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
		click = self.transformCoordsToTrue(*click)
		dx = abs( self.trueX - click[0] )
		dy = abs( self.trueY - click[1] )
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

			self.trueX += (click[0] - self.x) / self.zframe.imgscale
			self.trueY += (click[1] - self.y) / self.zframe.imgscale
			self.x, self.y = self.transformTrueToCoords(self.trueX, self.trueY)

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
				'path': self.path,
				'defaultTraceName': 'tongue',
				'traces': {
					'tongue': {
						'color': 'red',
						'files': {} } },
				'files': {} }

			# we want each object to have entries for everything here
			fileKeys = { '_prev', '_next', 'processed' } # and `processed`
			MIMEs = {
				'audio/x-wav'		:	['.wav'],
				'audio/x-flac'		:	['.flac'],
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

					MIME = getMIMEType(real_filepath)
					# print(MIME)
					if MIME in MIMEs:
						# add `good` files
						if extension in MIMEs[ MIME ]:
							if filename not in files:
								files[filename] = { key:None for key in fileKeys }
							files[filename][extension] = filepath
						elif MIME == 'text/plain' and extension == '.measurement':
							print('Found old measurement file {}'.format(filename))
							self.importOldMeasurement(filepath, filename)
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
		# print(filepath)
		open_file = json.load(open(filepath, 'r'))
		for key, value in open_file.items():
			if isinstance(value, dict):
				if 'type' in value.keys() and 'points' in value.keys():
					array = value['points']

		filenum, framenum = filename.split('_')
		# print('>>>>>>>', filenum, framenum)
		new_array = [{"x":point1,"y":point2} for point1, point2 in array]
		list_of_files = self.data['traces']['tongue']['files']
		if not filenum in list_of_files:
			list_of_files[filenum]={}
		list_of_files[filenum][framenum] = new_array

	def write(self, _mdfile=None):
		'''
		Write metadata out to file
		'''
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
		frame = self.app.frame if _frame==None else _frame
		processed = self.getFileLevel( 'processed' )
		try:
			return processed[str(frame-1)]
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
		elif key in mddict:
			return mddict[ key ]
		else:
			return None

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

	def getTraceCurrentFrame( self, trace ):
		'''
		Returns a list of the crosshairs for the given trace at the current file
		and current frame
		'''
		filename = self.getCurrentFilename()
		frame    = str(self.app.frame)
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
		self.write()

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
		self.frame.grid( row=0, column=0, sticky=W )
		self.TextGrid = None
		self.selectedTier = StringVar()

	def reset(self, event=None):
		'''
		Try to load a TextGrid file based on information stored in the metadata
		'''
		self.selectedTierFrames = []
		self.selectedItem = None
		if _TEXTGRID_LIBS_INSTALLED:
			# default Label in case there are errors below
			self.TkWidgets = [{ 'label':Label(self.frame, text="Unable to load TextGrid file") }]
			# the Data module will pass this filename=None if it can't find an appropriate .TextGrid file
			filename = self.app.Data.getFileLevel( '.TextGrid' )
			if filename:
				try:
					# self.boundaries = [] #for putting in the interval boundaries
					# try to load up our TextGrid using the textgrid lib
					self.TextGrid = TextGrid.fromFile( filename )
					# reset default Label to actually be useful
					self.TkWidgets = [{ 'label':Label(self.frame, text="TextGrid tiers:") }]
					# iterate the tiers
					self.frameTierName = self.getFrameTierName()
					for tier in self.TextGrid.getNames():
						if tier != self.frameTierName:
							# make some widgets for each tier
							tierWidgets = self.makeTierWidgets( tier )
							self.TkWidgets.append( tierWidgets )
					self.makeFrameWidget()
				except:
					pass
			# grid the widgets whether we loaded successfully or not
			self.grid()

	def getFrameTierName(self):
		'''
		Handle some inconsistency in how we're naming our alignment tier
		'''
		for name in _TEXTGRID_ALIGNMENT_TIER_NAMES:
			if name in self.TextGrid.getNames():
				return name
		raise NameError( 'Unable to find alignment tier' )

	def makeFrameWidget(self):
		frames_canvas = Canvas(self.frame, width=self.canvas_width, height=self.canvas_height, background='gray')
		self.TkWidgets.append({'frames':frames_canvas})
		tier = self.TextGrid.getFirst(self.frameTierName)

		# frames_canvas.create_line(0,self.canvas_height/2,self.canvas_width,self.canvas_height/2)
		#
		for point in tier:
			x_coord = point.time/self.TextGrid.maxTime*self.canvas_width
			frame = frames_canvas.create_line(x_coord, 0, x_coord, self.canvas_height, tags=point.mark)
			# if i%10==0:
			# 	frames_canvas.itemconfig(frame, fill='blue')

		frames_canvas.bind("<Button-1>", self.getClickedFrame)

	def getClickedFrame(self, event):
		'''
		Jumps to clicked frame
		'''
		item = self.my_find_closest(event)
		frame = event.widget.gettags(item)[0]
		self.app.frame = int(frame)
		if not frame in self.selectedTierFrames:
			self.selectedTierFrames = []
			self.wipeFill()
		self.app.framesUpdate()

	def makeTierWidgets(self, tier):
		'''
		Each tier should have two canvas widgets: `canvas-label` (the tier name),
		and `canvas` (the intervals on the tier with their marks)
		'''
		self.tier_pairs = {}

		self.canvas_width=700
		label_width=self.canvas_width/7
		self.canvas_height=60

		tier_obj = self.TextGrid.getFirst(tier)
		self.widgets = { #'label':Label(self.frame, text=('- '+tier+':'), wraplength=200, justify=LEFT),
						 'canvas-label':Canvas(self.frame, width=label_width, height=self.canvas_height),
						 # 'text' :Label(self.frame, text='', wraplength=550, justify=LEFT),
						 'canvas':Canvas(self.frame, width=self.canvas_width, height=self.canvas_height, background='gray')}

		canvas = self.widgets['canvas']
		label = self.widgets['canvas-label']
		tg_length=self.TextGrid.maxTime

		#builds tier label functionality
		label_text = label.create_text(label_width/2,self.canvas_height/2, justify=CENTER,
										text=tier+': ', width=label_width, activefill='blue')

		#puts numbers of frames contained in intervals into the tags of the text of teach interval
		intervals = [i for i in tier_obj]
		for interval in intervals:
			le_loc = interval.minTime/tg_length*self.canvas_width #x-coordinate for left edge of interval
			re_loc = interval.maxTime/tg_length*self.canvas_width #x-coordinate for right edge of interval
			# boundaries.append((le_loc, re_loc))
			intvl_length = re_loc-le_loc
			# print(interval, intvl_length)
			text = canvas.create_text(le_loc+(intvl_length/2), self.canvas_height/2, justify=CENTER,
								text=interval.mark, width=intvl_length, activefill='blue')
			if interval != intervals[-1]:
				canvas.create_line(re_loc,0,re_loc,self.canvas_height)
			#makes tag of text object into list of points within interval
			for point in self.TextGrid.getFirst(self.frameTierName):
				if interval.__contains__(point):
					canvas.addtag_withtag("frame"+point.mark, text)
					if interval.mark != '':
						label.addtag_withtag("frame"+point.mark, label_text)
				# print(canvas.gettags(label_text))
		#bindings
		canvas.bind("<Button-1>", self.genFrameList)
		self.app.bind("<Control-n>", self.zoomToInterval)
		self.app.bind("<Control-a>", self.zoomAll)
		self.app.bind("<Control-i>", self.zoomFactorOfTwo)
		self.app.bind("<Control-o>", self.zoomFactorOfTwo)
		label.bind("<Button-1>", self.genFrameList)
		# self.widgets['label'].bind("<Button-1>", self.genFrameList)

		return self.widgets

	def my_find_closest(self, event):
		'''
		replaces TkInter's find_closest function, which is buggy
		'''
		maybe_item = None
		dist = 999999999999
		for el in event.widget.find_all():
			obj_x = event.widget.coords(el)[0]
			if abs(obj_x-event.x) < dist:
				dist = abs(obj_x-event.x)
				maybe_item = el
		return maybe_item

	def wipeFill(self):
		'''
		turns selected frame back to black
		'''
		if self.selectedItem:
			self.selectedItem[0].itemconfig(self.selectedItem[1], fill='black')

	def genFrameList(self, event):
		'''
		Reads frames within interval from the tags to the text item of that interval,
		and highlights text of clicked interval
		'''
		self.wipeFill()
		# maybe_item = event.widget.find_closest(event.x, event.y) <<< has strange bug
		maybe_item = self.my_find_closest(event)

		if event.widget in self.tier_pairs.keys(): #if on tier-label canvas
			event.widget.itemconfig(maybe_item,fill='blue')
			self.selectedTierFrames = [x[5:] for x in event.widget.gettags(maybe_item)]
			#make all text intervals blue
			canvas = self.tier_pairs[event.widget]
			for el in canvas.find_all():
				if canvas.type(canvas.find_withtag(el)) == 'text':
					canvas.itemconfig(el, fill='blue')

		else: #on canvas with intervals/frames
			if isinstance(maybe_item, int):
				if maybe_item%2 == 0: #if item found is a boundary
					#determine on which side of the line the event occurred
					if event.widget.coords(maybe_item)[0] > event.x:
						# item = maybe_item+1 #righthand boundary drawn before text
						item = maybe_item-1
					else: #i.e. event was on line or to the right of it
						# item = maybe_item+3
						item = maybe_item+1
				else:
					item = maybe_item

				event.widget.itemconfig(item,fill='blue')
				self.selectedItem = (event.widget, item)
				self.selectedTierFrames = [x[5:] for x in event.widget.gettags(item)]

		#'current' automatically gets appended at the end of tags by tkinter, but we don't want it
		if 'nt' in self.selectedTierFrames:
			self.selectedTierFrames = self.selectedTierFrames[:-1]

		#automatically updates frame
		if not str(self.app.frame) in self.selectedTierFrames:
			if self.app.frame < int(self.selectedTierFrames[0]):
				self.app.framesNext()
				# self.update()
			elif self.app.frame > int(self.selectedTierFrames[-1]):
				self.app.framesPrev()
				# self.update()

	def zoomToInterval(self, event):
		'''

		'''
		visible = []
		#make sure that tier is selected
		if self.selectedItem == None:
			return
		widg = self.selectedItem[0]
		intvl_num = self.selectedItem[1]
		boundaries = (intvl_num-1, intvl_num+1)
		#x values of lines
		if boundaries[0] > 0:
			ledge = widg.coords(boundaries[0])[0]
		else:
			ledge = 0
		if boundaries[1] < len(widg.find_all()):
			redge =  widg.coords(boundaries[1])[0]
		else:
			redge = widg.find_all()[-1]

		self.zoomAll(ledge=ledge, redge=redge)

	def zoomFactorOfTwo(self, event):
		'''

		'''
		if event.keysym == 'i':
			pass
		elif event.keysym == 'o':
			pass

		self.zoomAll(ledge=ledge, redge=redge)

	def zoomAll(self, event=None, ledge=0, redge=None):
		'''

		'''
		if event:
			redge = self.canvas_width
		print(ledge, redge)
		sc_factor = redge-ledge

		#find items between edges
		for q, el in enumerate(self.TkWidgets):
			if 'canvas' in el or 'frames' in el:
				if 'canvas' in el:
					tier = el['canvas']
				elif 'frames' in el:
					tier = el['frames']
				items = []
				for item in tier.find_all():
					#if item in zoomed area
					if ledge < tier.coords(item)[0] < redge:
						loc = tier.coords(item)
						x = loc[0]
						new_x = (x-ledge)*(self.canvas_width/sc_factor)
						items.append((item,x,new_x))

				#include half-cut-off intervals CHECK IF THIS WORKS
				opnums=[]
				if 'canvas' in el and len(items) > 0:
					if tier.type(items[0][0]) == 'line':
						opnums.append(0)
					elif tier.type(items[-1][0]) == 'line':
						opnums.append(-1)
				for opnum in opnums:
					item = items[opnum][0]-1
					x = tier.coords(item)[0]
					new_x = (items[opnum][2]/2)
					items.append((item,x,new_x))

				#move to new position or delete
				for item in tier.find_all():
					item_nums = [i[0] for i in items]
					if item in item_nums:
						item = items[item_nums.index(item)]
						tier.move(item[0],item[2]-item[1], 0)
					else:
						tier.delete(item)


	# def update(self):
	# 	'''
	# 	Wrapper for updating the `text` Label widgets at a given frame number
	# 	'''
		# check that we've loaded a TextGrid
		# if self.TextGrid != None:
	# 		time = self.getTime( self.app.frame )
	# 		# update each of our tiers
	# 		for t in range(len( self.TextGrid.getNames() )):
	# 			tier = self.TextGrid.getNames()[t]
	# 			if tier != self.frameTierName:
	# 				# handy-dandy wrappers from the textgrid lib
	# 				interval = self.TextGrid.getFirst(tier).intervalContaining(time)
	# 				# need a +1 here because our default label actually sits at index 0
	# 				self.setTierText(t+1, interval.mark if (interval!=None) else "")

	# def getTime(self, frameNumber):
	# 	'''
	# 	Relies upon the existence of a dedicated tier mapping between the time in the
	# 	recording and the dicom frame at that time.  The name of this mapping tier is
	# 	set in self.load() (default='all frames')
	# 	'''
	# 	# check that we've loaded a TextGrid
	# 	if self.TextGrid != None:
	# 		if self.TextGrid.getFirst(self.frameTierName):
	# 			# NOTE: sometimes don't actually want first tier matching this name
	# 			# so we should be careful about the exact contents of the passed TextGrid file
	# 			points = self.TextGrid.getFirst(self.frameTierName)
	# 			if frameNumber < len(points):
	# 				#need a -1 because frameNumers start at 1
	# 				return points[frameNumber-1].time
	# 	# if we don't match all conditions, return a time value that will match no intervals
	# 	return -1

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
				tierWidgets['frames'].grid(row=t, column=1, sticky=W)
			if 'canvas' in tierWidgets:
				tierWidgets['canvas'].grid(row=t, column=1, sticky=W)
				tierWidgets['canvas-label'].grid(row=t, column=0, sticky=W)
				self.tier_pairs[tierWidgets['canvas-label']] = tierWidgets['canvas']

class TraceModule(object):
	'''
	Module to manage all of the different traces (with unique names/colors) and the
	Crosshairs objects associated to each one.  In particular, handles creation/modfication
	of traces and crosshairs.
	'''
	def __init__(self, app):
		print( ' - initializing module: Trace' )

		self.app = app

		# array of trace names for this directory
		self.available = self.app.Data.getTopLevel( 'traces' )
		self.available = [] if self.available==None else self.available

		# dictionary to hold trace -> [crosshairs] data
		self.crosshairs = {}

		# set of currently selected crosshairs
		self.selected = set()

		# declare & init trace string variable
		self.traceSV = StringVar()
		self.traceSV.set( '' )

		# frame for (most of) our widgets
		self.frame = Frame(self.app.LEFT, pady=7)
		self.frame.grid( row=4 )

		# listbox to contain all of our traces
		lbframe = Frame(self.frame)
		self.scrollbar = Scrollbar(lbframe)
		self.listbox = Listbox(lbframe, yscrollcommand=self.scrollbar.set, width=12)
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
			self.getWidget( Button(self.frame, text='Set as default', command=self.setDefaultTraceName), row=10, column=2, columnspan=2 ),
			self.getWidget( Button(self.frame, text='Select all', command=self.selectAll), row=11, column=2, columnspan=2 ),
			self.getWidget( Button(self.frame, text='Copy', command=self.copy), row=12, column=2 ),
			self.getWidget( Button(self.frame, text='Paste', command=self.paste), row=12, column=3 ),
			self.getWidget( Button(self.frame, text='Recolor', command=self.recolor), row=13, column=2, columnspan=2 ),
			self.getWidget( Button(self.frame, text='Clear', command=self.clear), row=15, column=2, columnspan=2 ),
			self.getWidget( Entry( self.frame, width=12, textvariable=self.traceSV), row=100, column=0, sticky=W ),
			self.getWidget( Button(self.frame, text='New', command=self.newTrace), row=100, column=2 ),
			self.getWidget( Button(self.frame, text='Rename', command=self.renameTrace), row=100, column=3 ) ]

		self.app.bind('<Control-r>', self.recolor )

	def update(self):
		''' on change frames '''
		self.grid()
		self.reset() # clear our crosshairs
		self.read()  # read from file
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
		write out the coordinates of all of our crosshairs to the metadata file
		'''

		trace = self.getCurrentTraceName()
		traces = []

		if trace in self.crosshairs:
			for ch in self.crosshairs[ trace ]:
				if ch.isVisible:
					x,y = ch.getTrueCoords()
					data = { 'x':x, 'y':y }
					if data not in traces:
						traces.append(data)
		self.app.Data.setCurrentTraceCurrentFrame( traces )

	def getCurrentTraceName(self):
		'''
		return string of current trace name
		'''

		try:
			return self.listbox.get(self.listbox.curselection())
		except _tkinter.TclError:
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

	def copy(self):
		''' TODO '''
		pass
	def paste(self):
		''' TODO '''
		pass
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
	Module to handle playback of audio files.

	Note: this module is sparse b/c most of it needs to be rewritten to depend on
		a more powerful audio manager
	'''
	def __init__(self, app):
		self.app = app
		self.current = None
		if _AUDIO_LIBS_INSTALLED:
			print( ' - initializing module: Audio' )
			self.mixer = pygame.mixer
			self.mixer.init()
			self.isPaused = False

			# widget management
			self.frame = Frame(self.app.BOTTOM)
			self.playBtn = Button(self.frame, text="Play/Pause", command=self.toggleAudio, state=DISABLED)
			self.app.bind('<space>', self.toggleAudio )

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
				self.mixer.music.load( audiofile )
				self.current = audiofile
				self.isPaused = False
				return True
			except:
				print('Unable to load audio file: `%s`' % audiofile)
				return False

	def toggleAudio(self, event=None):
		'''
		play/pause/stop
		'''
		if self.current != None:
			if self.isPaused:
				self.mixer.music.unpause()
				self.isPaused = False
			elif self.mixer.music.get_busy():
				self.mixer.music.pause()
				self.isPaused = True
			else:
				self.mixer.music.play()
				self.isPaused = False

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
			self.frame = Frame(self.app.LEFT, pady=7)
			self.frame.grid( row=2 )
			self.loadBtn = Button(self.frame, text='Load DICOM', command=self.process)
			self.loadBtn.grid()

			# zoom frame (contains our tracing canvas)
			self.zframe = ZoomFrame(self.app.RIGHT, 1.3)

			# reset zoom button
			self.zoomResetBtn = Button(self.app.LEFT, text='Reset image', command=self.zoomReset, pady=7 )

	def zoomReset(self, fromButton=True):
		'''
		reset zoom frame canvas and rebind it
		'''
		if self.isLoaded:
			# creates a new canvas object and we redraw everything to it
			self.zframe.resetCanvas( self.app.RIGHT )
			self.zframe.canvas.bind('<Button-1>', self.app.onClick )
			self.zframe.canvas.bind('<ButtonRelease-1>', self.app.onRelease )
			self.zframe.canvas.bind('<Motion>', self.app.onMotion )

	 		# we want to go here only after a button press
			if fromButton: self.app.framesUpdate()

	def update(self):
		'''
		change the image on the zoom frame
		'''
		if self.isLoaded:
			image = self.app.Data.getPreprocessedDicom()
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
				if processed == None:
					return self.process()
				else:
					self.app.frames = len(processed)

				# reset variables
				self.app.frame = 1
				self.isLoaded = True

				# update widgets
				self.frame.grid_remove()
				self.loadBtn.grid_remove()
				self.grid()
	def process(self):
		'''
		perform the dicom->PNG operation
		'''
		print( 'Reading DICOM data ...', end='\r' )

		if self.isLoaded == False:
			try:
				dicomfile = self.app.Data.getFileLevel( '.dicom' )
				self.dicom = dicom.read_file( dicomfile )

			except dicom.errors.InvalidDicomError:
				print( 'Unable to read DICOM file: %s' % dicomfile )
				return False

		pixels = self.dicom.pixel_array # np.array

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
			self.app.Data.getTopLevel('path'),
			self.app.Data.getFileLevel('name')+'_dicom_to_png' )
		if os.path.exists( outputpath ) == False:
			os.mkdir( outputpath )

		# grab one frame at a time to write (and provide a progress indicator)
		printProgressBar(0, frames, prefix = 'Processing:', suffix = 'complete')
		for f in range( frames ):

			printProgressBar(f+1, frames, prefix = 'Processing:', suffix = ('complete (%d of %d)' % (f+1,frames)))

			arr = pixels[ f,:,:,: ] if RGB else pixels[ f,:,: ]
			img = Image.fromarray( arr )

			outputfilename = '%s_frame_%04d.png' % ( self.app.Data.getFileLevel('name'), f )
			outputfilepath = os.path.join( outputpath, outputfilename )
			img.save( outputfilepath, format='PNG' )

			# keep track of all the processing we've finished
			processedData[ str(f) ] = outputfilepath

		self.app.Data.setFileLevel( 'processed', processedData )
		self.app.lift()
		self.load()

	def reset(self):
		'''
		new files should default to not showing dicom unless it has already been processed
		'''
		# hide frame navigation widgets
		self.grid_remove()

		self.isLoaded = False
		self.dicom = None

		# update buttons
		#print(self.app.Data.data['files'])
		if self.app.Data.getFileLevel( '.dicom' ) == None:
			self.loadBtn[ 'state' ] = DISABLED
		else:
			self.loadBtn[ 'state' ] = NORMAL
			# and check if data is already processed
			if self.app.Data.getFileLevel( 'processed' ) != None:
				self.load()
				self.zoomReset()

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
		self.app.bind('<Control-z>', self.undo )
		self.app.bind('<Control-Z>', self.redo )
		# also make some buttons and bind them
		self.frame = Frame(self.app.LEFT, pady=7)
		self.frame.grid( row=5 )
		self.undoBtn = Button(self.frame, text='Undo', command=self.undo)
		self.redoBtn = Button(self.frame, text='Redo', command=self.redo)
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

class App(Tk):
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
		super().__init__()

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
		self.Dicom = DicomModule(self)
		self.Trace = TraceModule(self)
		self.Audio = PlaybackModule(self)
		self.TextGrid = TextGridModule(self)

		print( ' - loading widgets' )

		self.filesUpdate()

		print()

	def setWidgetDefaults(self):
		'''
		Need to set up some defaults here before building Tk widgets (this is specifically
		true w/r/t the StringVars)
		'''
		self.currentFID = 0 	# file index w/in list of sorted files
		self.frame = 0			# current frame of dicom file
		self.isClicked = False	# used in handling of canvas click events
		self.isDragging = False # used in handling of canvas click events

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
		| |           - textgrid~              | |
		| |           - audio~                 | |
		| \____________________________________/ |
		\________________________________________/
		'''
		# main Frame skeleton
		self.TOP = Frame(self)
		self.LEFT = Frame(self.TOP)
		self.RIGHT = Frame(self.TOP)
		self.BOTTOM = Frame(self)
		self.TOP.grid(    row=0, column=0)
		self.LEFT.grid(   row=0, sticky=N )
		self.RIGHT.grid(  row=0, column=1 )
		self.BOTTOM.grid( row=1, column=0, columnspan=2 )

		# navigate between all available filenames in this directory
		self.filesFrame = Frame(self.LEFT, pady=7)
		self.filesPrevBtn = Button(self.filesFrame, text='<', command=self.filesPrev)
		self.filesJumpToMenu = OptionMenu(self.filesFrame, self.currentFileSV, *self.Data.files, command=self.filesJumpTo)
		self.filesNextBtn= Button(self.filesFrame, text='>', command=self.filesNext)
		self.filesFrame.grid( row=1 )
		self.filesPrevBtn.grid( row=1, column=0 )
		self.filesJumpToMenu.grid( row=1, column=1 )
		self.filesNextBtn.grid(row=1, column=2 )
		Header(self.filesFrame, text="Choose a file:").grid( row=0, column=0, columnspan=3 )

		# navigate between frames
		self.framesFrame = Frame(self.LEFT, pady=7)
		self.framesSubframe = Frame(self.framesFrame)
		self.framesPrevBtn = Button(self.framesSubframe, text='<', command=self.framesPrev)
		self.framesEntryText = Entry(self.framesSubframe, width=5, textvariable=self.frameSV)
		self.framesEntryBtn = Button(self.framesSubframe, text='Go', command=self.framesJumpTo)
		self.framesNextBtn= Button(self.framesSubframe, text='>', command=self.framesNext)
		self.framesHeader = Header(self.framesFrame, text="Choose a frame:")
		self.framesFrame.grid( row=3 )
		self.framesSubframe.grid( row=1 )

		# non-module-specific bindings
		self.bind('<Option-Left>', self.filesPrev )
		self.bind('<Option-Right>', self.filesNext )
		self.bind('<Left>', self.framesPrev )
		self.bind('<Right>', self.framesNext )
		self.bind('<BackSpace>', self.onBackspace )
		self.bind('<Configure>', self.onWindowResize )
		self.bind('<Escape>', self.onEscape )

		# force window to front
		self.lift()

	def lift(self):
		'''
		Bring window to front (doesn't shift focus to window)
		'''
		self.attributes('-topmost', 1)
		self.attributes('-topmost', 0)
	def onWindowResize(self, event):
		'''
		Handle moving or resizing the app window
		'''
		geometry = self.geometry()
		self.Data.setTopLevel( 'geometry', geometry )
	def onClick(self, event):
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

				# unselect crosshairs
				self.isClicked = True
				self.Trace.unselectAll()
				ch = self.Trace.add( *self.click )

				self.Control.push({ 'type':'add', 'chs':[ch] })

				return

			# NOTE: only get here if we clicked near something

			# if holding option key, unselect the guy we clicked on
			if event.state == 16:
				nearby.unselect()
				if nearby in self.Trace.selected:
					self.Trace.selected.remove( nearby )

			# otherwise, add it to our selection
			else:

				# check if we're holding shift key
				if event.state != 1 and nearby.isSelected == False:
					# if not, clear current selection
					self.Trace.unselectAll()

				# add this guy to our current selection
				nearby.select()
				self.Trace.select( nearby )

				# set dragging variables
				self.isDragging = True
				self.dragClick = self.click
	def onRelease(self, event):
		'''
		Handle releasing a click within the zoomframe canvas
		'''
		if self.Dicom.isLoaded:
			if self.isDragging:
				dx = (event.x - self.click[0])
				dy = (event.y - self.click[1])
			self.isDragging = False
			self.isClicked = False
			self.Trace.write()
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
		self.Dicom.reset() # need this after Trace.reset()
		self.Audio.reset()
		self.TextGrid.reset()

		# check if we can pan left/right
		self.filesPrevBtn['state'] = DISABLED if self.Data.getFileLevel('_prev')==None else NORMAL
		self.filesNextBtn['state'] = DISABLED if self.Data.getFileLevel('_next')==None else NORMAL
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
		# update variables
		self.frameSV.set( str(self.frame) )

		# update modules
		self.Control.update()
		self.Dicom.update()
		self.Trace.update()
		self.Audio.update()
		# self.TextGrid.update()

		# check if we can pan left/right
		self.framesPrevBtn['state'] = DISABLED if self.frame==1 else NORMAL
		self.framesNextBtn['state'] = DISABLED if self.frame==self.frames else NORMAL
	def framesPrev(self, event=None):
		'''
		controls self.framesPrevBtn for panning between frames
		'''
		if self.Dicom.isLoaded and self.frame > 1:
			self.frame -= 1
			if len(self.TextGrid.selectedTierFrames) != 0:
				while str(self.frame) not in self.TextGrid.selectedTierFrames:
					if self.frame <= int(self.TextGrid.selectedTierFrames[0]):
						self.frame = int(self.TextGrid.selectedTierFrames[0])
						break
					self.frame -= 1
			self.framesUpdate()
	def framesNext(self, event=None):
		'''
		controls self.framesNextBtn for panning between frames
		'''
		if self.Dicom.isLoaded and self.frame < self.frames:
			self.frame += 1
			if len(self.TextGrid.selectedTierFrames) != 0:
				while str(self.frame) not in self.TextGrid.selectedTierFrames:
					if self.frame >= int(self.TextGrid.selectedTierFrames[-1]):
						self.frame = int(self.TextGrid.selectedTierFrames[-1])
						break
					self.frame += 1
			self.framesUpdate()
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

if __name__=='__main__':
	app = App()
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
