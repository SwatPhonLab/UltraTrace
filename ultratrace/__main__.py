#!/usr/bin/env python3

#import modules
from . import modules
from . import util
from .util.logging import *
from .widgets import Header

import argparse
import os
import PIL

from tkinter.ttk import Button, Entry, Frame, OptionMenu
from tkinter import StringVar, Spinbox, Tk

try:
    from ttkthemes import ThemedTk
except ImportError as e:
    ThemedTk = Tk
    warn(e)

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
				info(' - loading platform-specific enhancements for Linux')
				import xrp  # pip3 install xparser
				from pathlib import Path
				XresPath = os.path.join(str(Path.home()), '.Xresources')
				if os.path.isfile(XresPath) or os.path.islink(XresPath):
					info("   - found .Xresources file: {}".format(XresPath))
					Xresources = xrp.parse_file(XresPath, encoding="utf8")
					#info("Opened .Xresources file {}".format(XresPath))
					if '*TtkTheme' in Xresources.resources:
						ttktheme = Xresources.resources['*TtkTheme']
						info("   - setting Linux Ttk theme to {}".format(ttktheme))
					elif '*TkTheme' in Xresources.resources:
						ttktheme = Xresources.resources['*TkTheme']
						info("   - setting Linux Tk theme to {}".format(ttktheme))
					else:
						ttktheme = "clam"  # alt, clam, classic, default
						info("   - falling back to default Linux Tk theme: {}.  You can set your theme to something else by adding a line like \"*TkTheme: alt\" or \"*TtkTheme: arc\" to ~/.Xresources".format(ttktheme))
				else:
					ttktheme = "clam"  # alt, clam, classic, default
					info("   - no ~/.Xresources file found; falling back to default Linux Tk theme: {}.  You can set your theme to something else by adding a line like \"*TkTheme: alt\" or \"*TtkTheme: arc\" to ~/.Xresources".format(ttktheme))
				super().__init__(theme=ttktheme)
			except Exception as e:
				error("Crash while loading .Xresources file or initialising T(t)k theme", e)
				super().__init__()
		else:
			super().__init__()
		self.title('UltraTrace')

		# check if we were passed a command line argument
		parser = argparse.ArgumentParser(prog='UltraTrace')
		parser.add_argument('path', help='path (unique to a participant) where subdirectories contain raw data', default=None, nargs='?')
		args = parser.parse_args()

		# initialize data module
		self.Data = modules.Metadata( self, args.path )

		# initialize the main app widgets
		self.setWidgetDefaults()
		self.buildWidgetSkeleton()

		# initialize other modules
		self.Control = modules.Control(self)
		self.Trace = modules.Trace(self)
		self.Dicom = modules.Dicom(self)
		self.Audio = modules.Playback(self)
		self.TextGrid = modules.TextGrid(self)
		self.Spectrogram = modules.Spectrogram(self)
		self.Search = modules.Search(self)

		info( ' - loading widgets' )

		self.filesUpdate()
		# self.framesUpdate()
		# self.TextGrid.startup() #NOTE why does modules.TextGrid have to reset a second time? Is there a more economical way to do this?


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
		# self.TOP.grid(    row=0, column=0, sticky='nw')
		# self.LEFT.grid(   row=0, sticky='n' )
		# self.RIGHT.grid(  row=0, column=1)
		# self.BOTTOM.grid( row=1, column=0, sticky='e')
		self.TOP.grid(    row=0, column=0, sticky='nesw')
		self.LEFT.grid(   row=0, sticky='nesw' )
		self.RIGHT.grid(  row=0, column=1, sticky='nesw')
		self.BOTTOM.grid( row=1, column=0, sticky='nesw')
		self.pady=3
		self.columnconfigure(0,weight=1)
		self.rowconfigure(0,weight=1)

		# navigate between all available filenames in this directory
		self.filesFrame = Frame(self.LEFT)#, pady=7)
		self.filesPrevBtn = Button(self.filesFrame, text='<', command=self.filesPrev, takefocus=0)
		self.filesJumpToMenu = OptionMenu(self.filesFrame, self.currentFileSV, self.Data.files[0], *self.Data.files, command=self.filesJumpTo)
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
		if util.get_platform() == 'Linux':
			self.bind('<Control-Left>', self.filesPrev )
			self.bind('<Control-Right>', self.filesNext )
		else:
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
				tierWidgets['frames-label'].coords('all',(self.leftwidth,tierWidgets['frames-label'].coords(1)[1]))
			if 'canvas' in tierWidgets:
				tierWidgets['canvas-label'].config(width=self.leftwidth)
				tierWidgets['canvas-label'].coords('all',(self.leftwidth,tierWidgets['canvas-label'].coords(1)[1]))
		if event == None or event.widget == self:
			self.alignBottomRight(self.winfo_width() - self.leftwidth)
			if self.Dicom.zframe.image:
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
		if self.Dicom.isLoaded():
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
		if self.Dicom.isLoaded():

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
			# self.TextGrid.start = float(min(t1,t2))
			# self.TextGrid.end = float(max(t1,t2))
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
				# debug(canvas.gettags('all'))
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
		if self.Dicom.isLoaded():

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
		self.filesPrevBtn['state'] = 'disabled' if self.Data.getFileLevel('_prev')==None else 'normal'
		self.filesNextBtn['state'] = 'disabled' if self.Data.getFileLevel('_next')==None else 'normal'
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
		self.framesPrevBtn['state'] = 'disabled' if self.frame==self.TextGrid.startFrame else 'normal'
		self.framesNextBtn['state'] = 'disabled' if self.frame==self.TextGrid.endFrame else 'normal'

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

if __name__=='__main__':
	app = App()
	# app.mainloop()
	while True:
		try:
			app.mainloop()
			break
		except UnicodeDecodeError as e:
			error(e)
