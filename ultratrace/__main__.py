#!/usr/bin/env python3

#import modules
from . import modules
from . import util
from .util.logging import *
from .widgets import Header

import argparse
import os
import PIL

import wx

class Frame(wx.Frame):
	
	def __init__(self, parent, title):
		super(Frame, self).__init__(parent, title=title)

		info( 'initializing UltraTrace' )

		self.initialise()

	def initialise(self):

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
		#self.Control = modules.Control(self)
		#self.Trace = modules.Trace(self)
		#self.Dicom = modules.Dicom(self)
		#self.Audio = modules.Playback(self)
		#self.TextGrid = modules.TextGrid(self)
		#self.Spectrogram = modules.Spectrogram(self)
		#self.Search = modules.Search(self)

		info( ' - loading widgets' )

		#self.filesUpdate()

		# to deal with resize handler being called multiple times
		# in a single window resize
		self.isResizing = False

		#self.oldwidth = self.winfo_width()

		#self.after(300,self.afterstartup)

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

		# some styling
		#self.fontStyle = Style()
		#if util.get_platform() == 'Darwin':
		#	self.fontStyle.configure('symbol.TButton', font=('DejaVu Serif', 26))
		#else:
		#	self.fontStyle.configure('symbol.TButton', font=('DejaVu Serif', 19))

		# declare string variables
		#self.currentFileSV = StringVar(self)
		#self.frameSV = StringVar(self)

		# initialize string variables
		self.currentFileSV = self.Data.files[ self.currentFID ]
		self.frameSV = '1'

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
		panel = wx.Panel(self)
		hbox = wx.BoxSizer(wx.HORIZONTAL)
		self.grid = wx.FlexGridSizer(2, 2, 2, 2)
		
		#self.TOP = wx.Panel(self)
		#self.TOP = Frame(self)
		#self.TOP.columnconfigure(1,weight=1, minsize=320)
		#self.TOP.rowconfigure(0,weight=1, minsize=240)
		#self.LEFT = Frame(self.TOP)
		## self.LEFT.rowconfigure(0,weight=1)
		## self.LEFT.columnconfigure(0,weight=1)
		#self.RIGHT = Frame(self.TOP)
		#self.RIGHT.rowconfigure(0,weight=1)
		#self.RIGHT.columnconfigure(0,weight=1)
		#self.BOTTOM = Frame(self)
		## self.BOTTOM.columnconfigure(0,weight=1)
		#self.BOTTOM.columnconfigure(1,weight=1)
		## self.BOTTOM.rowconfigure(0,weight=1)
		## self.TOP.grid(    row=0, column=0, sticky='nw')
		## self.LEFT.grid(   row=0, sticky='n' )
		## self.RIGHT.grid(  row=0, column=1)
		## self.BOTTOM.grid( row=1, column=0, sticky='e')
		#self.TOP.grid(    row=0, column=0, sticky='nesw')
		#self.LEFT.grid(   row=0, sticky='nesw' )
		#self.RIGHT.grid(  row=0, column=1, sticky='nesw')
		#self.BOTTOM.grid( row=1, column=0, sticky='nesw')
		#self.pady=3
		#self.columnconfigure(0,weight=1)
		#self.rowconfigure(0,weight=1)
		#text1 = wx.StaticText(panel, label="controls here")
		text2 = wx.StaticText(panel, label="US here")
		text3 = wx.StaticText(panel, label="labels here")
		text4 = wx.StaticText(panel, label="audio and textgrids here")

		self.controlBox = wx.BoxSizer(wx.VERTICAL)
		####  Buttons
		####  FileSelectorBox
		##### FileControlBox
		self.fileControlBox = wx.BoxSizer(wx.HORIZONTAL)
		self.fileSelectorOpen = wx.Button(self, id=wx.ID_OPEN)#, style=wx.BU_NOTEXT)
		self.fileControlBox.Add(self.fileSelectorOpen)

		self.fileSelectorBox = wx.StaticBoxSizer(wx.VERTICAL, self, label="Files")
		self.fileSelectorBox.Add(self.fileControlBox)
		self.fileSelector = wx.ListCtrl(self, -1, style=wx.LC_REPORT)
		self.fileSelector.InsertColumn(0, 'name', width=50)
		self.fileSelector.InsertColumn(1, 'annotated', wx.LIST_FORMAT_RIGHT, width=50)
		self.fileSelector.InsertItem(0, 'test')

		self.fileSelectorBox.Add(self.fileSelector, 1, wx.EXPAND)

		####  FrameSelectorBox
		self.frameSelectorBox = wx.StaticBoxSizer(wx.HORIZONTAL, self, label="Frames")
		self.frameSelectorPrev = wx.Button(self, label="<", style=wx.BU_EXACTFIT)
		self.frameSelectorText = wx.TextCtrl(self, style=wx.TE_RIGHT, value=self.frameSV)
		self.frameSelectorNext = wx.Button(self, label=">", style=wx.BU_EXACTFIT)
		self.buttonPlayPause = wx.Button(self, label="⏯")# style=wx.BU_EXACTFIT)
		self.setCharSize(self.frameSelectorNext, 1)
		self.setCharSize(self.frameSelectorText, 5)
		self.setCharSize(self.frameSelectorPrev, 1)
		self.setCharSize(self.buttonPlayPause, 3)

		#self.frameSelectorBox.AddMany([(self.frameSelectorPrev),(self.frameSelectorText),(self.frameSelectorNext),(self.buttonPlayPause)])
		self.frameSelectorBox.Add(self.frameSelectorPrev, flag=wx.LEFT, border=10)
		self.frameSelectorBox.Add(self.frameSelectorText)
		self.frameSelectorBox.Add(self.frameSelectorNext, flag=wx.RIGHT, border=10)
		self.frameSelectorBox.Add(self.buttonPlayPause, border=10)

		####  AnnotationsBox
		self.annotationsBox = wx.StaticBoxSizer(wx.HORIZONTAL, self, label="Annotations")
		self.buttonSelectAll = self.newIconButton(wx.ID_SELECTALL, "gtk-select-all")
		self.buttonCopy = self.newIconButton(wx.ID_COPY, wx.ART_COPY)
		self.buttonPaste = self.newIconButton(wx.ID_PASTE, wx.ART_PASTE) #wx.Button(self, id=wx.ID_PASTE, style=wx.BU_NOTEXT | wx.BU_EXACTFIT)
		self.buttonDelete = self.newIconButton(wx.ID_DELETE, wx.ART_DELETE) #wx.Button(self, id=wx.ID_DELETE, style=wx.BU_NOTEXT | wx.BU_EXACTFIT)
		self.buttonZoomIn = self.newIconButton(wx.ID_ZOOM_IN, "gtk-zoom-in") #wx.Button(self, id=wx.ID_ZOOM_IN, style=wx.BU_NOTEXT | wx.BU_EXACTFIT)
		self.buttonZoomOut = self.newIconButton(wx.ID_ZOOM_OUT, "gtk-zoom-out") #wx.Button(self, id=wx.ID_ZOOM_OUT, style=wx.BU_NOTEXT | wx.BU_EXACTFIT)
		self.buttonZoomFit = self.newIconButton(wx.ID_ZOOM_FIT, "gtk-zoom-fit") #wx.Button(self, id=wx.ID_ZOOM_FIT, style=wx.BU_NOTEXT | wx.BU_EXACTFIT)
		self.buttonUndo = self.newIconButton(wx.ID_UNDO, wx.ART_UNDO)
		self.buttonRedo = self.newIconButton(wx.ID_REDO, wx.ART_REDO)

		#self.annotationsBox.AddMany([(self.buttonSelectAll),(self.buttonCopy),(self.buttonPaste),(self.buttonDelete)])
		self.annotationsBox.Add(self.buttonSelectAll, flag=wx.LEFT, border=10)
		self.annotationsBox.Add(self.buttonCopy, flag=wx.BOTTOM, border=10)
		self.annotationsBox.Add(self.buttonPaste)
		self.annotationsBox.Add(self.buttonDelete)
		self.annotationsBox.Add((20,0))
		self.annotationsBox.Add(self.buttonUndo)
		self.annotationsBox.Add(self.buttonRedo, flag=wx.RIGHT, border=10)


		####  ViewBox
		self.viewBox = wx.StaticBoxSizer(wx.HORIZONTAL, self, label="View")
		self.viewBox.Add(self.buttonZoomIn, flag=wx.LEFT, border=10)
		self.viewBox.Add(self.buttonZoomOut, flag=wx.BOTTOM, border=10)
		self.viewBox.Add(self.buttonZoomFit, flag=wx.RIGHT, border=10)

		####  LayersBox
		self.layersBox = wx.StaticBoxSizer(wx.VERTICAL, self, label="Labels")
		#self.layersBox = 
		self.layersBox = wx.StaticBoxSizer(wx.VERTICAL, self, label="")
		self.layers = wx.ListCtrl(self, -1, style=wx.LC_REPORT)
		self.layers.InsertColumn(0, 'name', width=60)
		self.layers.InsertColumn(1, 'default', wx.LIST_FORMAT_RIGHT, width=30)
		self.layers.InsertColumn(2, 'visible', wx.LIST_FORMAT_RIGHT, width=30)
		self.layers.InsertColumn(3, 'colour', wx.LIST_FORMAT_RIGHT, width=30)
		self.layers.InsertColumn(4, 'delete', wx.LIST_FORMAT_RIGHT, width=30)
	#	self.layers.InsertItem(0, "test")
		self.il = wx.ImageList(16,16)
		#il.Add(wx.ArtProvider.GetBitmap("gtk-emblem-default",wx.ART_MENU))
		#hargle = self.il.Add(wx.ArtProvider.GetBitmap("gtk-zoom-in",wx.ART_MENU))
		self.ICON_DEFAULT = self.il.Add(wx.ArtProvider.GetBitmap("emblem-default",wx.ART_MENU))
		self.layers.AssignImageList(self.il, wx.IMAGE_LIST_SMALL)
		thisLayer = self.newLayer(self.layers, "text", "#008888", default=True)
		self.layersBox.Add(self.layers)


		## add all sections to the control box
		self.controlBox.AddMany([(self.fileSelectorBox, 1, wx.EXPAND), ((0,10)), (self.frameSelectorBox,0,wx.EXPAND), ((0,10)), (self.annotationsBox, 0, wx.EXPAND), ((0,10)), (self.viewBox,0,wx.EXPAND), ((0,10)), (self.layersBox,0,wx.EXPAND)])

		self.grid.AddMany([(self.controlBox, 1, wx.EXPAND), (text2, 1, wx.EXPAND), (text3), (text4)])

		self.grid.AddGrowableRow(0,1)
		self.grid.AddGrowableCol(0,1)

		hbox.Add(self.grid, proportion=1, flag=wx.ALL|wx.EXPAND, border=2)
		panel.SetSizer(hbox)
		panel.Fit()
		## navigate between all available filenames in this directory
		#self.filesFrame = Frame(self.LEFT)#, pady=7)
		#self.filesPrevBtn = Button(self.filesFrame, text='<', command=self.filesPrev, takefocus=0, width="1.5")
		#self.filesJumpToMenu = OptionMenu(self.filesFrame, self.currentFileSV, self.Data.files[0], *self.Data.files, command=self.filesJumpTo)
		#self.filesNextBtn= Button(self.filesFrame, text='>', command=self.filesNext, takefocus=0, width="1.5")
		#self.filesFrame.grid( row=1 )
		#self.filesPrevBtn.grid( row=1, column=0 )
		#self.filesJumpToMenu.grid( row=1, column=1 )
		#self.filesNextBtn.grid(row=1, column=2 )
		#Header(self.filesFrame, text="Recording").grid( row=0, column=0, columnspan=3 )

		## navigate between frames
		#self.framesFrame = Frame(self.LEFT)#, pady=7)
		#self.framesSubframe = Frame(self.framesFrame)
		#self.framesPrevBtn = Button(self.framesSubframe, text='<', command=self.framesPrev, takefocus=0, width="1.5")
		#self.framesEntryText = Entry(self.framesSubframe, width=5, textvariable=self.frameSV)
		#self.framesEntryBtn = Button(self.framesSubframe, text='Go', command=self.framesJumpTo, takefocus=0, width="3")
		#self.framesNextBtn= Button(self.framesSubframe, text='>', command=self.framesNext, takefocus=0, width="1.5")
		#self.framesHeader = Header(self.framesFrame, text="Frame")
		#self.framesFrame.grid( row=3 )
		#self.framesSubframe.grid( row=1 )

		## non-module-specific bindings
		#if util.get_platform() == 'Linux':
		#	self.bind('<Control-Left>', self.filesPrev )
		#	self.bind('<Control-Right>', self.filesNext )
		#else:
		#	self.bind('<Option-Left>', self.filesPrev )
		#	self.bind('<Option-Right>', self.filesNext )
		#self.bind('<Left>', self.framesPrev )
		#self.bind('<Right>', self.framesNext )
		#self.bind('<BackSpace>', self.onBackspace )
		#self.bind('<Button-1>', self.getWinSize)
		#self.bind('<ButtonRelease-1>', self.onRelease)
		#self.bind('<Double-Button-1>', self.onDoubleClick)
		#self.bind('<Escape>', self.onEscape )
		## self.count = 0

		#self.framesEntryText.bind('<Return>', self.unfocusAndJump)
		#self.framesEntryText.bind('<Escape>', lambda ev: self.framesFrame.focus())

		# force window to front
		#self.lift()

	def setCharSize(self, obj, sizeInChar):
		size = obj.GetSizeFromTextSize(obj.GetTextExtent('9'*sizeInChar))
		obj.SetInitialSize(size)
		obj.SetSize(size)

	def newIconButton(self, wxId, wxBmp):
		button = wx.Button(self, id=wxId, style=wx.BU_NOTEXT | wx.BU_EXACTFIT)
		button.SetBitmapLabel(wx.ArtProvider.GetBitmap(wxBmp,wx.ART_MENU))
		return button

	def newLayer(self, layers, name, colour, default=False):
		item = layers.InsertItem(layers.GetItemCount(), name)
		#layers.SetItemBackgroundColour(item, wx.Colour(colour))
		if default:
			layers.SetItem(item, 1, "", self.ICON_DEFAULT)
		layers.SetItem(item, 2, "👁")
		(w, h) = (16, 16)
		clr = PIL.ImageColor.getcolor(colour, "RGBA")
		bmp2 = wx.Bitmap.FromRGBA(w, h, clr[0], clr[1], clr[2], clr[3])
		###bmp = wx.EmptyBitmap(w, h)
		###dc = wx.MemoryDC(bmp)
		###dc.SetPen(wx.Pen(wx.RED,1))
		###dc.DrawPolygon([(0,0),(0,10),(10,10),(10,0)], fill_style=wx.WINDING_RULE)
		###box = dc.GetAsBitmap()
		###dc.SelectObject(wx.NullBitmap)
		boxIdx = self.il.Add(bmp2)
		layers.SetItem(item, 3, "", boxIdx)
		return item

	def lift(self):
		'''
		Bring window to front (doesn't shift focus to window)
		'''
		self.attributes('-topmost', 1)
		self.attributes('-topmost', 0)

	def update(self):
		pass

	def geometry(self):
		pass



if __name__=='__main__':
	# app.mainloop()
	app = wx.App()
	mainFrame = Frame(None, title='UltraTrace')
	mainFrame.Show()
	while True:
		try:
			app.MainLoop()
			break
		except:
			print("crashed")
		#except UnicodeDecodeError as e:
		#	error(e)
