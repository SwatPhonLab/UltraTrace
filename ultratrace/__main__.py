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
		text1 = wx.StaticText(panel, label="controls here")
		text2 = wx.StaticText(panel, label="US here")
		text3 = wx.StaticText(panel, label="labels here")
		text4 = wx.StaticText(panel, label="audio and textgrids here")

		self.controlBox = wx.BoxSizer(wx.VERTICAL)
		####
		self.fileSelectorBox = wx.StaticBoxSizer(wx.VERTICAL, self, label="Files")
		self.fileSelector = wx.ListCtrl(self, -1, style=wx.LC_REPORT)
		self.fileSelector.InsertColumn(0, 'name', width=40)
		self.fileSelector.InsertColumn(1, 'annotated', wx.LIST_FORMAT_RIGHT, width=10)
		self.fileSelector.InsertItem(0, 'test')

		self.fileSelectorBox.Add(self.fileSelector, 1, wx.EXPAND)
		####
		
		self.controlBox.AddMany([(self.fileSelectorBox, 1, wx.EXPAND)])

		self.grid.AddMany([(self.controlBox, 1, wx.EXPAND), (text2, 1, wx.EXPAND), (text3), (text4)])

		self.grid.AddGrowableRow(0,1)
		self.grid.AddGrowableCol(0,1)

		hbox.Add(self.grid, proportion=1, flag=wx.ALL|wx.EXPAND, border=2)
		panel.SetSizer(hbox)
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
