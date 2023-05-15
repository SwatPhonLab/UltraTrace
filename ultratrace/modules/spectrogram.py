import wx
import wx.lib.agw.floatspin as FS
from .base import Module
from ..util.logging import *
import numpy as np
import parselmouth
from PIL import Image
import math

import matplotlib
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure

LIBS_INSTALLED = False

try:
    import numpy as np
    import parselmouth
    LIBS_INSTALLED = True

except ImportError as e:
    warn(e)


class Spectrogram(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        
        info(' - initializing module: Spectrogram')

        self.app = parent

        self.figure = Figure()
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.canvas.SetBackgroundColour('blue')

        self.spectrogram = None

        self.clicktime = -1
        self.specClick = False
        self.oldSelected = None

        # Create a vertical sizer to manage the layout of child widgets
        vertical_sizer = wx.BoxSizer(wx.VERTICAL)

        # Create a horizontal sizer to contain the vertical sizer and the canvas
        horizontal_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Create spin controls (the wxPython equivalent of Tkinter's Spinbox)
        self.axis_ceil_box = FS.FloatSpin(self, -1, min_val=0, max_val=100000, increment=100, value=0, agwStyle=FS.FS_LEFT)
        self.wl_box = FS.FloatSpin(self, -1, min_val=0, max_val=1, increment=0.0005, value=0, agwStyle=FS.FS_LEFT)
        self.dyn_range_box = FS.FloatSpin(self, -1, min_val=0, max_val=10000, increment=10, value=0, agwStyle=FS.FS_LEFT)

        self.doDefaults()
        self.axis_ceil_box.Bind(wx.EVT_SPINCTRL, self.drawSpectrogram)
        self.wl_box.Bind(wx.EVT_SPINCTRL, self.drawSpectrogram)
        self.dyn_range_box.Bind(wx.EVT_SPINCTRL, self.drawSpectrogram)

        # Create buttons
        self.default_btn = wx.Button(self, label='Standards')
        self.apply_btn = wx.Button(self, label='Apply')

        self.default_btn.Bind(wx.EVT_BUTTON, self.restoreDefaults)
        self.apply_btn.Bind(wx.EVT_BUTTON, self.drawSpectrogram)

        # Add the spin controls and buttons to the vertical sizer
        vertical_sizer.Add(self.axis_ceil_box, 0, wx.EXPAND | wx.ALL, 5)
        vertical_sizer.Add(self.wl_box, 0, wx.EXPAND | wx.ALL, 5)
        vertical_sizer.Add(self.dyn_range_box, 0, wx.EXPAND | wx.ALL, 5)
        vertical_sizer.Add(self.default_btn, 0, wx.EXPAND | wx.ALL, 5)
        vertical_sizer.Add(self.apply_btn, 0, wx.EXPAND | wx.ALL, 5)

        # Add the vertical sizer and the canvas to the horizontal sizer
        horizontal_sizer.Add((400,0))
        horizontal_sizer.Add(vertical_sizer, 0, wx.EXPAND | wx.ALL, 5)
        horizontal_sizer.Add(self.canvas, 1, wx.EXPAND | wx.ALL, 5)

        # Set the horizontal sizer as the main sizer for the panel
        self.SetSizer(horizontal_sizer)
        self.Fit()


        # Bind event handlers or configure the canvas as needed
        self.canvas.Bind(wx.EVT_LEFT_DOWN, self.jumpToFrame)

    def drawSpectrogram(self, event=None):
        x = np.arange(0, 3, 0.01)
        y = np.sin(np.pi * x)
        self.axes.plot(x, y)
        self.canvas.draw()




    def doDefaults(self):
        self.axis_ceil_box.SetValue(5000.0)
        self.wl_box.SetValue(0.005)
        self.dyn_range_box.SetValue(90.0)

    def restoreDefaults(self, event):
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

    # def drawSpectrogram(self, event=None):
    #     x = np.arange(0,3,0.01)
    #     y = np.sin(np.pi*x)
    #     self.axes.plot(x,y)

    # def drawSpectrogram(self, event=None):
    #     '''
    #     Extracts spectrogram data from sound, and draws it to canvas
    #     '''
    #     if not LIBS_INSTALLED:
    #         return

    #     if self.app.Audio.current:
    #         sound = parselmouth.Sound(self.app.Audio.current)
    #         self.canvas.Refresh()

    #         ts_fac = 10000.0
    #         wl = self.wl_box.GetValue()
    #         screen_start = self.app.TextGrid.start
    #         screen_end = self.app.TextGrid.end
    #         screen_duration = screen_end - screen_start
    #         audio_start = 0
    #         audio_end = sound.get_total_duration()
    #         real_start = max(screen_start, audio_start)
    #         real_end = min(screen_end, audio_end)
    #         duration = real_end - real_start

    #         if duration <= 0:
    #             return

    #         self.ts = duration / ts_fac
    #         extra = self.ts * math.floor(wl / self.ts)
    #         start_time = max(0, real_start - extra)
    #         end_time = min(real_end + extra, sound.get_total_duration())
    #         sound_clip = sound.extract_part(from_time=start_time, to_time=end_time)

    #         spec = sound_clip.to_spectrogram(window_length=wl, time_step=self.ts, maximum_frequency=self.axis_ceil_box.GetValue())
    #         self.spectrogram = 10 * np.log10(np.flip(spec.values, 0))

    #         mx = self.spectrogram.max()
    #         dyn = self.dyn_range_box.GetValue()
    #         self.spectrogram = self.spectrogram.clip(mx-dyn, mx) - mx
    #         self.spectrogram *= (-255.0 / dyn)

    #         img = Image.fromarray(self.spectrogram)
    #         if img.mode != 'RGB':
    #             img = img.convert('RGB')
    #         img = img.resize((int(self.canvas_width*(duration / screen_duration)), self.canvas_height))

    #         wximage = wx.Image(img.size[0], img.size[1])
    #         wximage.SetData(img.tobytes())
    #         wxbitmap = wx.Bitmap(wximage)

    #         dc = wx.BufferedDC(wx.ClientDC(self.canvas))
    #         dc.Clear()
    #         dc.DrawBitmap(wxbitmap, 0, 0)

    #         if self.app.TextGrid.selectedItem:
    #             tags = self.app.TextGrid.selectedItem[0].gettags(self.app.TextGrid.selectedItem[1])
    #         coord = self.canvas_width
    #         coord *= 1 - ((screen_end - real_end) / screen_duration)
    #         dc.DrawBitmap(wxbitmap, coord, self.canvas_height)

    #         # Rest of the code...

    # # Rest of the class...



    def drawInterval(self):
        '''
        Adapted with permission from
        https://courses.engr.illinois.edu/ece590sip/sp2018/spectrograms1_wideband_narrowband.html
        by Mark Hasegawa-Johnson
        '''
        if self.app.TextGrid.selectedItem:
            widg = self.app.TextGrid.selectedItem[0]
            itm = self.app.TextGrid.selectedItem[1]

        if widg in self.app.TextGrid.tier_pairs:  # if widg is label
            itvl_canvas = self.app.TextGrid.tier_pairs[widg]
            for i in itvl_canvas.find_withtag('line'):
                loc = itvl_canvas.coords(i)[0]
                self.canvas.DrawLine(loc, 0, loc, self.canvas_height)
        elif widg in self.app.TextGrid.tier_pairs.values():  # if widg is textgrid canvas
            if itm - 1 in widg.FindObjects():
                l_loc = widg.GetPosition(itm - 1)[0]
                self.canvas.DrawLine(l_loc, 0, l_loc, self.canvas_height)
            if itm + 1 in widg.FindObjects():
                r_loc = widg.GetPosition(itm + 1)[0]
                self.canvas.DrawLine(r_loc, 0, r_loc, self.canvas_height)
        elif widg == self.canvas:
            l_time, r_time = self.app.TextGrid.getMinMaxTime()
            l_loc = self.timeToX(float(l_time))
            r_loc = self.timeToX(float(r_time))
            self.canvas.DrawLine(l_loc, 0, l_loc, self.canvas_height)
            self.canvas.DrawLine(r_loc, 0, r_loc, self.canvas_height)

        # draw selected frame
        if self.app.TextGrid.firstFrame <= self.app.frame <= self.app.TextGrid.lastFrame:
            xcoord = self.app.TextGrid.frames_canvas.GetPosition(self.app.TextGrid.highlighted_frame)[0]
            self.canvas.DrawLine(xcoord, 0, xcoord, self.canvas_height)
        # draw line where user last clicked on spectrogram
        if self.clicktime != -1 and self.specClick == False:
            x = self.timeToX(self.clicktime)
            self.canvas.DrawLine(x, 0, x, self.canvas_height)


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
        self.canvas.grid(row=0, column=0, sticky='news')
        self.spinwin.grid(row=0,column=0,sticky='ne')
        # self.axis_canvas.grid(row=0,column=0,sticky='se')

    def grid_remove(self):
        self.canvas.grid_remove()
        self.spinwin.grid_remove()
