from .base import Module
import tkinter as tk

class Spectrogram(Module):
    def __init__(self,app):
        self.frame = tk.Frame(self.app.BOTTOM)
        self.frame.grid( row=0, column=1, pady=(self.app.pady*2,self.app.pady/2) )
        self.axis_frame = tk.Frame(self.app.BOTTOM)
        self.axis_frame.grid( row=0, column=0, sticky='e', pady=(self.app.pady*2,self.app.pady/2) )
        self.canvas = tk.Canvas(self.frame, width=self.canvas_width, height=self.canvas_height, background='gray', highlightthickness=0)
        self.spec_freq_max = tk.DoubleVar()
        self.wl = tk.DoubleVar()
        self.dyn_range = tk.DoubleVar()
        self.spinwin = tk.Frame(self.axis_frame)
        axis_ceil_box = tk.Spinbox(self.spinwin, textvariable=self.spec_freq_max, command=self.drawSpectrogram, width=7, increment=100, from_=0, to_=100000)
        axis_ceil_box.bind('<Return>',self.drawSpectrogram)
        axis_ceil_box.bind('<Escape>',lambda ev: self.spinwin.focus())
        wl_box = tk.Spinbox(self.spinwin, textvariable=self.wl, command=self.drawSpectrogram, width=7, increment=0.0005, from_=0, to_=1)
        wl_box.bind('<Return>',self.drawSpectrogram)
        wl_box.bind('<Escape>',lambda ev: self.spinwin.focus())
        dyn_range_box = tk.Spinbox(self.spinwin, textvariable=self.dyn_range, command=self.drawSpectrogram, width=7, increment=10, from_=0, to_=10000)
        dyn_range_box.bind('<Return>',self.drawSpectrogram)
        dyn_range_box.bind('<Escape>',lambda ev: self.spinwin.focus())
        default_btn = tk.Button(self.spinwin, text='Standards', command=self.restoreDefaults, takefocus=0)
        apply_btn = tk.Button(self.spinwin, text='Apply', command=self.drawSpectrogram, takefocus=0)
        axis_ceil_box.grid(row=0, columnspan=2, sticky='ne')
        wl_box.grid(row=1, columnspan=2, sticky='ne')
        dyn_range_box.grid(row=2, columnspan=2, sticky='ne')
        default_btn.grid(row=3)
        apply_btn.grid(row=3, column=1)
        self.canvas.bind('<Button-1>', self.jumpToFrame)

    def doDefaults(self):
        self.spec_freq_max.set(5000.0)
        self.wl.set(0.005)
        self.dyn_range.set(90)

    def update(self):
        self.canvas.delete('line')

    def drawSpectrogram(self, event=None):
        self.canvas.config(height=self.canvas_height)
        self.canvas.delete('all')
        img = self.canvas.create_image(self.canvas_width, self.canvas_height, anchor='se', image=photo_img)

    def drawInterval(self):
        # leaving this ....
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
        x = self.canvas.canvasx(event.x)

    def grid(self):
        self.canvas.grid(row=0, column=0, sticky='news')
        self.spinwin.grid(row=0,column=0,sticky='ne')

    def grid_remove(self):
        self.canvas.grid_remove()
        self.spinwin.grid_remove()
