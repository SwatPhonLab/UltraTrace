import wx
from .base import Module
from .. import util
from ..util.logging import *
from ..widgets import CanvasTooltip
import copy
import tempfile

LIBS_INSTALLED = False

try:
    from textgrid import TextGrid as TextGridFile, IntervalTier, PointTier, Point # textgrid
    from textgrid.exceptions import TextGridError
    LIBS_INSTALLED = True
except ImportError as e:
    warn(e)

ALIGNMENT_TIER_NAMES = [ 'frames', 'all frames', 'dicom frames', 'ultrasound frames' ]

class TextGrid(Module):
    '''
    Manages all the widgets related to TextGrid files, including the tier name
    and the text content of that tier at a given frame
    '''
    def __init__(self, app):
        '''
        Keep a reference to the master object for binding the widgets we create
        '''
        info(' - initializing module: TextGrid')
        self.app = app
        self.frame = self.app.audioTGPanel
        self.label_padx = 0
        self.canvas_frame = self.app.audioTGPanel
        self.TextGrid = None
        self.selectedTier = ""
        self.tg_zoom_factor = 1.5
        self.canvas_width = 800
        self.canvas_height = 60
        self.collapse_height = 15
        self.selectedIntvlFrames = []
        self.selectedItem = None
        self.start = 0
        self.end = 0
        self.current = 0
        self.frame_shift = 0.00

        self.startup()

        platform = util.get_platform()
        #bindings
        if platform == 'Linux':
            pass
        # TODO: Add more bindings as needed
    def setup(self):
        '''
        Set up the TextGrid widgets
        '''
        # Create the main panel for the TextGrid
        self.panel = wx.Panel(self.frame)

        # Create the tier name label
        self.tierNameLabel = wx.StaticText(self.panel, label="Tier Name:")

        # Create the tier name entry
        self.tierNameEntry = wx.TextCtrl(self.panel, size=(200, -1))

        # Create the text content label
        self.textContentLabel = wx.StaticText(self.panel, label="Text Content:")

        # Create the text content entry
        self.textContentEntry = wx.TextCtrl(self.panel, size=(200, -1))

        # Create the canvas for the TextGrid
        self.canvas = wx.Panel(self.panel, size=(self.canvas_width, self.canvas_height))
        self.canvas.SetBackgroundColour(wx.Colour(255, 255, 255))

        # TODO: Add more widgets as needed

        # Set up the layout using sizers
        self.setup_layout()

        # Bind events
        self.bind_events()

    def bind_events(self):
        '''
        Bind events for the TextGrid widgets
        '''
        self.tierNameEntry.Bind(wx.EVT_TEXT, self.on_tier_name_change)
        self.textContentEntry.Bind(wx.EVT_TEXT, self.on_text_content_change)
        # TODO: Bind more events as needed

    def setup_layout(self):
        '''
        Set up the layout for the TextGrid widgets using sizers
        '''
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Tier name layout
        tier_name_sizer = wx.BoxSizer(wx.HORIZONTAL)
        tier_name_sizer.Add(self.tierNameLabel, 0, wx.ALL, 5)
        tier_name_sizer.Add(self.tierNameEntry, 1, wx.ALL | wx.EXPAND, 5)
        main_sizer.Add(tier_name_sizer, 0, wx.ALL | wx.EXPAND, 5)

        # Text content layout
        text_content_sizer = wx.BoxSizer(wx.HORIZONTAL)
        text_content_sizer.Add(self.textContentLabel, 0, wx.ALL, 5)
        text_content_sizer.Add(self.textContentEntry, 1, wx.ALL | wx.EXPAND, 5)
        main_sizer.Add(text_content_sizer, 0, wx.ALL | wx.EXPAND, 5)

        # Canvas layout
        main_sizer.Add(self.canvas, 1, wx.ALL | wx.EXPAND, 5)

        # TODO: Add more sizers as needed

        self.panel.SetSizer(main_sizer)
        self.panel.Layout()

