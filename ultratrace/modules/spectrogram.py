from .base import Module
from ..util.logging import *

import math
import PIL

from tkinter.ttk import Button, Frame
from tkinter import Canvas, DoubleVar
try:
    # ttk.Spinbox was added in Python 3.7
    from tkinter.ttk import Spinbox
except ImportError:
    from tkinter import Spinbox

LIBS_INSTALLED = False

try:
    import numpy as np
    import parselmouth
    from PIL import ImageTk
    LIBS_INSTALLED = True
except ImportError as e:
    warn(e)


class Spectrogram(Module):
    def __init__(self, app):
        info(' - initializing module: Spectrogram')

        self.app = app

        self.frame = Frame(self.app.BOTTOM)
        self.frame.grid(row=0, column=1, pady=(self.app.pady * 2, self.app.pady / 2))
        self.axis_frame = Frame(self.app.BOTTOM)
        self.axis_frame.grid(row=0, column=0, sticky='e', pady=(self.app.pady * 2, self.app.pady / 2))
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

        # make spinboxes & buttons for spectrogram specs
        self.spinwin = Frame(self.axis_frame)
        # spinboxes
        axis_ceil_box = Spinbox(self.spinwin, textvariable=self.spec_freq_max, command=self.drawSpectrogram, width=7, increment=100, from_=0, to_=100000)
        axis_ceil_box.bind('<Return>', self.drawSpectrogram)
        axis_ceil_box.bind('<Escape>', lambda ev: self.spinwin.focus())
        wl_box = Spinbox(self.spinwin, textvariable=self.wl, command=self.drawSpectrogram, width=7, increment=0.0005, from_=0, to_=1)
        wl_box.bind('<Return>', self.drawSpectrogram)
        wl_box.bind('<Escape>', lambda ev: self.spinwin.focus())
        dyn_range_box = Spinbox(self.spinwin, textvariable=self.dyn_range, command=self.drawSpectrogram, width=7, increment=10, from_=0, to_=10000)
        dyn_range_box.bind('<Return>', self.drawSpectrogram)
        dyn_range_box.bind('<Escape>', lambda ev: self.spinwin.focus())
        # buttons
        default_btn = Button(self.spinwin, text='Standards', command=self.restoreDefaults, takefocus=0)
        apply_btn = Button(self.spinwin, text='Apply', command=self.drawSpectrogram, takefocus=0, width=6)

        # self.axis_frame.create_window(wwidth,self.canvas_height, window=self.spinwin, anchor='ne')
        # grid spinboxes & buttons on subframe
        axis_ceil_box.grid(row=0, columnspan=2, sticky='ne')
        wl_box.grid(row=1, columnspan=2, sticky='ne')
        dyn_range_box.grid(row=2, columnspan=2, sticky='ne')
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
        if not LIBS_INSTALLED:
            return

        if self.app.Audio.current:
            sound = parselmouth.Sound(self.app.Audio.current)
            self.canvas.delete('all')

            ts_fac = 10000.0
            wl = self.wl.get()
            screen_start = self.app.TextGrid.start
            screen_end = self.app.TextGrid.end
            screen_duration = screen_end - screen_start
            audio_start = 0
            audio_end = sound.get_total_duration()
            real_start = max(screen_start, audio_start)
            real_end = min(screen_end, audio_end)
            duration = real_end - real_start

            if duration <= 0:
                return

            self.ts = duration / ts_fac
            # the amount taken off in spectrogram creation seems to be
            # ( 2 * ts * floor( wl / ts ) ) + ( duration % ts )
            # but we've defined ts as duration / 10000, so duration % ts = 0
            # so the amount to increase the length by is ts * floor( wl / ts )
            # at either end - D.S.
            extra = self.ts * math.floor(wl / self.ts)
            start_time = max(0, real_start - extra)
            end_time = min(real_end + extra, sound.get_total_duration())
            sound_clip = sound.extract_part(from_time=start_time, to_time=end_time)

            spec = sound_clip.to_spectrogram(window_length=wl, time_step=self.ts, maximum_frequency=self.spec_freq_max.get())
            self.spectrogram = 10 * np.log10(np.flip(spec.values, 0))

            # self.spectrogram += self.spectrogram.min()
            # self.spectrogram *= (60.0 / self.spectrogram.max())

            mx = self.spectrogram.max()
            dyn = self.dyn_range.get()
            # debug(self.spectrogram.min(), self.spectrogram.max())
            self.spectrogram = self.spectrogram.clip(mx - dyn, mx) - mx
            # debug(self.spectrogram.min(), self.spectrogram.max())
            self.spectrogram *= (-255.0 / dyn)
            # self.spectrogram += 60
            # debug(self.spectrogram.min(), self.spectrogram.max())

            img = PIL.Image.fromarray(self.spectrogram)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            # contrast = ImageEnhance.Contrast(img)
            # img = contrast.enhance(5)
            # self.canvas_height = img.height
            img = img.resize((int(self.canvas_width * (duration / screen_duration)), self.canvas_height))

            photo_img = ImageTk.PhotoImage(img)
            self.canvas.config(height=self.canvas_height)

            # self.canvas.create_image(0,0, anchor='nw', image=photo_img)
            # self.canvas.create_image(self.canvas_width/2,self.canvas_height/2, image=photo_img)
            if self.app.TextGrid.selectedItem:
                tags = self.app.TextGrid.selectedItem[0].gettags(self.app.TextGrid.selectedItem[1])
            coord = self.canvas_width
            coord *= 1 - ((screen_end - real_end) / screen_duration)
            img = self.canvas.create_image(coord, self.canvas_height, anchor='se', image=photo_img)
            self.img = photo_img
            # pass on selected-ness
            if self.app.TextGrid.selectedItem:
                if self.app.TextGrid.selectedItem[0] == self.canvas:
                    self.app.TextGrid.selectedItem = (self.canvas, img)
                    # pass on tags
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

            if widg in self.app.TextGrid.tier_pairs:  # if widg is label
                itvl_canvas = self.app.TextGrid.tier_pairs[widg]
                for i in itvl_canvas.find_withtag('line'):
                    loc = itvl_canvas.coords(i)[0]
                    self.canvas.create_line(loc, 0, loc, self.canvas_height, tags='line', fill='blue')
            elif widg in self.app.TextGrid.tier_pairs.values():  # if widg is textgrid canvas
                if itm - 1 in widg.find_all():
                    l_loc = widg.coords(itm - 1)[0]
                    self.canvas.create_line(l_loc, 0, l_loc, self.canvas_height, tags='line', fill='blue')
                if itm + 1 in widg.find_all():
                    r_loc = widg.coords(itm + 1)[0]
                    self.canvas.create_line(r_loc, 0, r_loc, self.canvas_height, tags='line', fill='blue')
            elif widg == self.canvas:
                l_time, r_time = self.app.TextGrid.getMinMaxTime()
                l_loc = self.timeToX(float(l_time))
                r_loc = self.timeToX(float(r_time))
                self.canvas.create_line(l_loc, 0, l_loc, self.canvas_height, tags='line', fill='blue')
                self.canvas.create_line(r_loc, 0, r_loc, self.canvas_height, tags='line', fill='blue')

            # draw selected frame
            if self.app.TextGrid.firstFrame <= self.app.frame <= self.app.TextGrid.lastFrame:
                xcoord = self.app.TextGrid.frames_canvas.coords(self.app.TextGrid.highlighted_frame)[0]
                self.canvas.create_line(xcoord, 0, xcoord, self.canvas_height, tags='line', fill='red')
            # draw line where user last clicked on spectrogram
            if self.clicktime != -1 and self.specClick == False:
                x = self.timeToX(self.clicktime)
                self.canvas.create_line(x, 0, x, self.canvas_height, tags='line', fill='green')

    def jumpToFrame(self, event):
        '''  '''
        # restore textgrid selected interval between clicks
        if not self.app.TextGrid.selectedItem:
            key = next(iter(self.app.TextGrid.tier_pairs))
            wdg = self.app.TextGrid.tier_pairs[key]
            self.app.TextGrid.selectedItem = (wdg, wdg.find_all()[0])
            self.app.TextGrid.setSelectedIntvlFrames(self.app.TextGrid.selectedItem)
        if self.app.TextGrid.selectedItem[0] == self.canvas:
            self.app.TextGrid.selectedItem = self.oldSelected
            self.app.TextGrid.setSelectedIntvlFrames(self.app.TextGrid.selectedItem)
        # prevents wiping of canvases because of mouse click
        # self.app.resized = False
        # draw line at click location
        x = self.canvas.canvasx(event.x)
        self.clicktime = self.xToTime(x)
        # jump to new frame
        frame = self.app.TextGrid.my_find_closest(self.app.TextGrid.frames_canvas, self.canvas.canvasx(event.x))
        framenum = self.app.TextGrid.frames_canvas.gettags(frame)[0][5:]
        self.app.frame = int(framenum)
        self.app.framesUpdate()
        # remember which interval was selected before specgram click
        if event.state == 1:
            self.oldSelected = self.app.TextGrid.selectedItem
        # for selecting & zooming interval (w/ shift)
            self.specClick = True

    def xToTime(self, x):
        ''' converts from a x coordinate (relative to the canvas) to the timestamp at that coordinate'''
        return (x * float(self.app.TextGrid.end - self.app.TextGrid.start) / self.canvas_width) + float(self.app.TextGrid.start)

    def timeToX(self, time):
        ''' converts from a time to the x coordinate on a canvas representing that time'''
        return self.canvas_width * (time - float(self.app.TextGrid.start)) / float(self.app.TextGrid.end - self.app.TextGrid.start)

    def grid(self):
        '''
        Put tkinter items on app
        '''
        self.canvas.grid(row=0, column=0, sticky='news')
        self.spinwin.grid(row=0, column=0, sticky='ne')
        # self.axis_canvas.grid(row=0,column=0,sticky='se')

    def grid_remove(self):
        self.canvas.grid_remove()
        self.spinwin.grid_remove()
