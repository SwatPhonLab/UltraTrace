#!/usr/bin/env python3

import argparse
import wx

import modules
from logging import info


class Frame(wx.Frame):
    def __init__(self, parent, title):
        super().__init__(parent, title=title)
        info('Initializing UltraTrace')
        self.initialise()

    def initialise(self):
        parser = argparse.ArgumentParser(prog='UltraTrace')
        parser.add_argument('path', help='Path (unique to a participant) where subdirectories contain raw data',
                            default=None, nargs='?')
        args = parser.parse_args()

        self.Data = modules.Metadata(self, args.path)

        self.set_widget_defaults()
        self.build_widget_skeleton()

        self.Trace = modules.Trace(self)
        self.Dicom = modules.Dicom(self)
        self.Audio = modules.Playback(self)
        self.TextGrid = modules.TextGrid(self)

        info('Loading widgets')

        self.is_resizing = False

    def set_widget_defaults(self):
        self.current_fid = 0
        self.frame = 0
        self.is_clicked = False
        self.is_dragging = False
        self.current_path = ''

    def build_widget_skeleton(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.Trace, 1, wx.EXPAND)
        main_sizer.Add(self.Dicom, 1, wx.EXPAND)
        main_sizer.Add(self.Audio, 0, wx.EXPAND)
        main_sizer.Add(self.TextGrid, 0, wx.EXPAND)
        self.SetSizer(main_sizer)
        self.SetAutoLayout(1)
        self.Show()


app = wx.App(False)
frame = Frame(None, 'UltraTrace')
app.MainLoop()
