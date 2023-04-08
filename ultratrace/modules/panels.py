import wx
from ..util.logging import *

# based on https://discuss.wxpython.org/t/within-frame-should-i-use-panels-or-not-to-contain-items/34818/2

class Panel_root(wx.Panel):
	def __init__(self, parent):
		info( ' - initialising layout' )
		self.Data = parent.Data
		self.frameSV = parent.frameSV
		self.app = parent

		wx.Panel.__init__(self, parent)
		self.app.controlPanel = control_panel(self)
		self.app.ultrasoundPanel = ultrasound_panel(self)
		self.app.audioTGPanel = textgrid_panel(self)

		controls_and_us = wx.BoxSizer(wx.HORIZONTAL)
		controls_and_us.Add(self.app.controlPanel, 1, wx.EXPAND)
		controls_and_us.Add(self.app.ultrasoundPanel, 1, wx.EXPAND)

		root_sizer = wx.BoxSizer(wx.VERTICAL)
		root_sizer.Add(controls_and_us, 3, wx.EXPAND)
		root_sizer.Add(self.app.audioTGPanel, 1, wx.EXPAND)

class control_panel(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)

		self.Data = parent.Data
		self.frameSV = parent.frameSV
		
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
		self.fileSelector.InsertColumn(0, 'name', width=200)
		self.fileSelector.InsertColumn(1, 'annotated', wx.LIST_FORMAT_RIGHT, width=50)
		#self.fileSelector.InsertItem(0, 'test')
		for filedata in self.Data.files:
			self.fileSelector.InsertItem(self.fileSelector.GetItemCount(), filedata)

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
		#self.buttonCopy = wx.Button(self, id=wx.ID_COPY, style=wx.BU_NOTEXT | wx.BU_EXACTFIT)
		#self.buttonCopy = wx.BitmapButton(self, id=wx.ID_COPY, bitmap=wx.ArtProvider.GetBitmap(wx.ART_COPY), size=(32,32))
		self.buttonPaste = self.newIconButton(wx.ID_PASTE, wx.ART_PASTE) #wx.Button(self, id=wx.ID_PASTE, style=wx.BU_NOTEXT | wx.BU_EXACTFIT)
		#self.buttonPaste = wx.BitmapButton(self, id=wx.ID_PASTE, bitmap=wx.ArtProvider.GetBitmap(wx.ART_PASTE), size=(32,32))
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
		#self.layersBox = wx.StaticBoxSizer(wx.VERTICAL, self, label="Layers")

		## add all sections to the control box
		self.controlBox.AddMany([
			(self.fileSelectorBox, 1, wx.EXPAND), ((0,10)),
			(self.frameSelectorBox, 0, wx.EXPAND), ((0,10)),
			(self.annotationsBox, 0, wx.EXPAND), ((0,10)),
			(self.viewBox, 0, wx.EXPAND), ((0,10))
		])#(self.layersBox,0,wx.EXPAND)])

		#self.grid.AddMany([(self.controlBox, 1, wx.EXPAND), (self.ultrasoundBox, 1, wx.EXPAND), (text3), (self.audioTGBox)])

		#self.grid.AddGrowableRow(0,1)
		#self.grid.AddGrowableCol(0,1)

		#self.hbox.Add(self.grid, proportion=1, flag=wx.ALL|wx.EXPAND, border=2)
		#self.SetSizer(self.hbox)
		#self.SetSizerAndFit(self.controlBox)
		self.SetSizer(self.controlBox)
		self.Fit()

	def setCharSize(self, obj, sizeInChar):
		size = obj.GetSizeFromTextSize(obj.GetTextExtent('9'*sizeInChar))
		obj.SetInitialSize(size)
		obj.SetSize(size)

	def newIconButton(self, wxId, wxBmp):
		#button = wx.Button(self, id=wxId, style=wx.BU_NOTEXT | wx.BU_EXACTFIT)
		#button.SetBitmapLabel(wx.ArtProvider.GetBitmap(wxBmp,wx.ART_MENU))
		button = wx.BitmapButton(self, id=wxId, bitmap=wx.ArtProvider.GetBitmap(wxBmp), size=(32,32))
		return button

class ultrasound_panel(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)
		self.SetBackgroundColour(wx.YELLOW)

class textgrid_panel(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)
		self.SetBackgroundColour(wx.GREEN)

