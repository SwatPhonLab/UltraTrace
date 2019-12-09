from .base import Module
from ..widgets import CanvasTooltip
import tkinter as tk

class TextGrid(Module):
    def __init__(self, app):
        self.frame = tk.Frame(self.app.BOTTOM)
        self.canvas_frame = tk.Frame(self.app.BOTTOM)
        self.frame.grid( row=1, column=0, sticky='ne')
        self.canvas_frame.grid(row=1, column=1 )
        self.selectedTier = tk.StringVar()
        self.frame_shift = tk.DoubleVar()

        platform = util.get_platform()
        if platform == 'Linux':
            mod = 'Control'
            alt = 'Command'
        elif platform == 'Darwin':
            mod = 'Command'
            alt = 'Option'
        else:
            mod = 'Command'
            alt = 'Command'

        self.app.bind(f"<{mod}-n>", self.getBounds)
        self.app.bind(f"<{mod}-a>", self.getBounds)
        self.app.bind(f"<{mod}-i>", self.getBounds)
        self.app.bind(f"<{mod}-o>", self.getBounds)
        self.app.bind(f"<{mod}-f>", self.openSearch)
        self.app.bind(f"<{alt}-Up>", self.changeTiers)
        self.app.bind(f"<{alt}-Down>", self.changeTiers)
        self.app.bind(f"<{alt}-Left>", self.changeIntervals)
        self.app.bind(f"<{alt}-Right>", self.changeIntervals)
        self.app.bind("<Shift-Left>", self.getBounds)
        self.app.bind("<Shift-Right>", self.getBounds)

    def startup(self):
        self.TkWidgets = [{ 'label':tk.Label(self.frame, text="Unable to load TextGrid file") }]

    def makeTimeWidget(self):
        self.time_canvas = tk.Canvas(self.canvas_frame, width=self.canvas_width, height=self.canvas_height/3, highlightthickness=0)
        s = self.time_canvas.create_text(3,0, anchor='nw', text=self.start)
        e = self.time_canvas.create_text(self.canvas_width,0, anchor='ne', text=self.end)
        c = self.time_canvas.create_text(self.canvas_width/2,0, anchor='n', text=self.current)
        self.TkWidgets.append({'times':self.time_canvas})

    def makeFrameWidget(self):
        self.frames_canvas = tk.Canvas(self.canvas_frame, width=self.canvas_width, height=self.canvas_height, background='gray', highlightthickness=0)
        frames_label = tk.Canvas(self.frame, width=self.label_width, height=self.canvas_height, highlightthickness=0, background='gray')
        frames_label.create_text(self.label_width,0, anchor='ne', justify='center', text='frames: ', width=self.label_width, activefill='blue')
        sbframe = tk.Frame(frames_label)
        go_btn = tk.Button(sbframe, text='Offset', command=self.shiftFrames, takefocus=0)
        txtbox = tk.Spinbox(sbframe, textvariable=self.frame_shift, width=7, from_=-10000000, to=10000000)
        txtbox.bind('<Escape>', lambda ev: sbframe.focus())
        txtbox.bind('<Return>', lambda ev: self.shiftFrames())
        go_btn.grid(row=0, column=0, sticky='e')
        txtbox.grid(row=0, column=1, sticky='e')
        window = frames_label.create_window(self.label_width*.3,self.canvas_height/3, anchor='nw', window=sbframe)
        self.TkWidgets.append({'name':self.frameTierName,'frames':self.frames_canvas, 'frames-label':frames_label})
        self.frames_canvas.bind("<Button-1>", self.getClickedFrame)

    def makeTierWidgets(self, tier):
        widgets = { 'name':tier,
                     'canvas-label':tk.Canvas(self.frame, width=self.label_width, height=self.canvas_height, highlightthickness=0),
                     'canvas':tk.Canvas(self.canvas_frame, width=self.canvas_width, height=self.canvas_height, background='gray', highlightthickness=0)}
        label_text = label.create_text(self.label_width, self.canvas_height/2, anchor='e', justify='center',
                                        text='temp', width=self.label_width/2, activefill='blue')
        canvas.bind("<Button-1>", self.genFrameList)
        label.bind("<Button-1>", self.genFrameList)
        label.bind("<Double-Button-1>", self.collapse)
        label.bind("<Button-4>", self.collapse)
        label.bind("<Button-5>", self.collapse)
        label.bind("<MouseWheel>", self.collapse)
        canvas.bind("<Button-4>", self.collapse)
        canvas.bind("<Button-5>", self.collapse)
        canvas.bind("<MouseWheel>", self.collapse)

    def fillCanvases(self):
        canvas.delete('all')
        text = canvas.create_text(loc, self.canvas_height/2, justify='center',
        text=tier[i].mark, width=pixel_length, activefill='blue')
        canvas.addtag_withtag(minTimetag, text)
        canvas.addtag_withtag(maxTimetag, text)
        canvas.addtag_withtag("frame"+self.frameTier[frame_i].mark, text)
        el['canvas-label'].addtag_all("frame"+self.frameTier[frame_i].mark)
        frames = el['frames']
        frames.delete('all')
        frame = frames.create_line(x_coord, 0, x_coord, self.canvas_height, tags="frame"+tier[i].mark, fill=fill)
        CanvasTooltip(frames, frame,text=tier[i].mark)

    def updateTimeLabels(self):
        self.TkWidgets[-1]['times'].itemconfig(1,text='{:.6f}'.format(self.start))
        self.TkWidgets[-1]['times'].itemconfig(2,text='{:.6f}'.format(self.end))
        self.TkWidgets[-1]['times'].itemconfig(3,text='{:.6f}'.format(self.current))

    def updateTierLabels(self):
        current_label = el['canvas-label'].find_all()[0]
        nonempty_frames = el['canvas-label'].gettags(current_label)
        el['canvas-label'].itemconfig(current_label, text='{}:\n({}/{})'.format(el['name'],len(self.getTracedFrames(nonempty_frames)), len(nonempty_frames)))

    def wipeFill(self):
        '''
        Turns selected frame and interval back to black
        '''
        self.frames_canvas.itemconfig('frame'+str(frame), fill=fill)
        wdg.itemconfig(itm, fill='black')
        if len(wdg.find_withtag(itm+1)) > 0:
            wdg.itemconfig(itm+1, fill='black')
        if len(wdg.find_withtag(itm-1)) > 0:
            wdg.itemconfig(itm-1, fill='black')
        if wdg in self.tier_pairs.keys():
            wdg.itemconfig(1, fill='black')
            self.tier_pairs[wdg].itemconfig('all', fill='black')
            self.frames_canvas.itemconfig('all', fill='black')

    def genFrameList(self, event=None, widg=None, x_loc=None, SI=False):
        framenum = self.frames_canvas.gettags(frame)[0][5:]

    def collapse(self, event):
        l.configure(height=h)
        c.configure(height=h)
        l.move('all', 0, mv)
        self.app.event_generate('<Configure>')

    def paintCanvases(self):
        if wdg.type(itm) == 'text':
            wdg.itemconfig(itm, fill='blue')
            if itm+1 in wdg.find_all():
                wdg.itemconfig(itm+1, fill='blue')
            if itm-1 in wdg.find_all():
                wdg.itemconfig(itm-1, fill='blue')
        if wdg in self.tier_pairs.keys():
            canvas = self.tier_pairs[wdg]
            for el in canvas.find_all():
                canvas.itemconfig(el, fill='blue')
        frames = wdg.gettags(itm)
        for frame in frames:
            frame_obj = self.frames_canvas.find_withtag(frame)
            self.frames_canvas.itemconfig(frame_obj, fill=fill)
        self.highlighted_frame = self.frames_canvas.find_withtag('frame'+str(self.app.frame))
        self.frames_canvas.itemconfig(self.highlighted_frame, fill='red')

    def update(self):
        if "frame"+str(self.app.frame) not in self.selectedItem[0].gettags(self.selectedItem[1]):
            new_interval = widg.find_withtag("frame"+str(self.app.frame))[0]

    def grid(self, event=None):
        for t in range(len(self.TkWidgets)):
            tierWidgets = self.TkWidgets[t]
            if 'label' in tierWidgets:
                tierWidgets['label'].grid(row=t, column=0, sticky='w')
            if 'frames' in tierWidgets:
                tierWidgets['frames'].grid(row=t, column=2, sticky='w', pady=self.app.pady)
                tierWidgets['frames-label'].grid(row=t, column=0, sticky='w', pady=self.app.pady)
            if 'canvas' in tierWidgets:
                tierWidgets['canvas'].grid(row=t, column=2, sticky='w', pady=self.app.pady/2)
                tierWidgets['canvas-label'].grid(row=t, column=0, sticky='w', pady=self.app.pady/2)
                self.tier_pairs[tierWidgets['canvas-label']] = tierWidgets['canvas']
            if 'times' in tierWidgets:
                tierWidgets['times'].grid(row=t, column=2, sticky='s')

