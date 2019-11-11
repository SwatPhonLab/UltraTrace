_CROSSHAIR_DRAG_BUFFER,
_CROSSHAIR_SELECT_RADIUS,
_TEXTGRID_ALIGNMENT_TIER_NAMES,

Unknown = object

# B1 event: Left-click
# Scroll event: <MouseWheel>, <Button-4>/<Button-5>

class ZoomFrame(tk.Frame):
    def __init__(self, Frame: master, Unknown: delta, App: app):
        # set self.{app, delta, maxZoom, canvas_width, width, canvas_height, height, shown, aspect_ratio,
        self.canvas = tk.Canvas(
                master,
                bg='grey',
                width=canvas_wdith,
                height=canvas_height,
                hightlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky='news')

        rect = RectTracker(self.canvas)
        rect.autodraw(outline='blue')

        self.canvas.bind(
                ('Ctrl+B1', self.moveFrom),
                ('Ctrl+B1Motion', self.moveTo),
                ('Scroll', self.wheel))

        self.resetCanvas()

        self.canvas.bind(
                ('B1', app.onClickZoom),
                ('Motion', app.onMotion))
        self.app.bind(
                ('Cmd+=', self.wheel),
                ('Cmd+-', self.wheel))

    def resetCanvas(self):
        raise NotImplementedError()

    def setImage(self, PIL.Image: image):
        raise NotImplementedError()

    def showImage(self, tk.Event: _event = None):
        raise NotImplementedError()

    def wheel(self, tk.Event: event):
        raise NotImplementedError()

    def scrollY(self, *args, **kwargs):
        self.canvas.yview(*args, **kwargs)
        self.showImage()

    def moveFrom(self, tk.Event: event):
        self.panStartX = event.x
        self.panStartY = event.y

    def moveTo(self, tk.Event: event):
        dx = event.x - self.panStartX
        dy = event.y - self.panStartY
        self.panStartX = event.x
        self.panStartY = event.y
        self.panX += dx
        self.panY += dy
        self.showImage()

class Header(tk.Label):
    def __init__(self, tk.Frame: master, str: text):
        Label.__init__(self, master, text=text, font='TkDefaultFont 12 bold')

class RectTracker:
    raise NotImplementedError()

class Crosshairs:
    def __init__(self, ZoomFrame: zframe, float: x, float: y, str: color, bool: transform = True):
        self.zframe = zframe
        # set (un)selected(Color|Width) and defaultLength
        self.trueX = self.x = x
        self.trueY = self.y = y
        if transform:
            self.trueX, self.trueY = self.transformCoordsToTrue(x, y)
        else:
            self.x, self.y = self.transformTrueToCoords(x, y)
        self.len = self.transformLength(self.defaultLength)
        self.isSelected = False
        self.isVisible = True
        self.hline = self.zframe.canvas.create_line(...)
        self.vline = self.zframe.canvas.create_line(...)

    def getTrueCoords(self):
        return self.trueX, self.trueY

    def transformCoordsToTrue(self, x, y):
        return ((x - self.zframe.panX) / (self.zframe.width * self.zframe.imgscale),
                (y - self.zframe.panY) / (self.zframe.height * self.zframe.imgscale))

    def transformTrueToCoords(self, trueX, trueY):
        return (trueX * self.zframe.width * self.zframe.imgscale + self.zframe.panX,
                trueY * self.zframe.height * self.zframe.imgscale + self.zframe.panY)

    def transformCoords(self, x, y):
        return (x + self.zframe.canvas.canvasx(0),
                y + self.zframe.canvas.canvasy(0))

    def transformLength(self, l):
        return l * self.zframe.imgscale

    def getDistance(self, Tuple<float,float>: click):
        if not self.isVisible:
            return float('inf')
        click = self.transformCoords(*click)
        dx = abs(self.x - click[0])
        dy = abs(self.y - click[1])
        return math.sqrt(dx**2, dy**2)

    def select(self):
        if self.isVisible:
            self.zframe.canvas.itemconfig(self.hline, ...)
            self.zframe.canvas.itemconfig(self.vline, ...)
            self.isSelected = True

    def unselect(self):
        if self.isVisible:
            self.zframe.canvas.itemconfig(self.hline, ...)
            self.zframe.canvas.itemconfig(self.vline, ...)
            self.isSelected = False

    def draw(self):
        self.zframe.canvas.itemconfig(self.hline, state='normal')
        self.zframe.canvas.itemconfig(self.hline, state='normal')
        self.isVisible = True

    def undraw(self):
        self.zframe.canvas.itemconfig(self.hline, state='hidden')
        self.zframe.canvas.itemconfig(self.hline, state='hidden')
        self.unselect()
        self.isVisible = False

    def dragTo(self, Tuple<float,float> click):
        is self.isVisible:
            self.x += (click[0] - self.x)
            self.y += (click[1] - self.y)
            self.trueX, self.trueY = self.transformCoordsToTrue(self.x, self.y)
            self.len = self.transformLength(self.defaultLength)
            self.zframe.canvas.coords(self.hline, ...)
            self.zframe.canvas.coords(self.vline, ...)

    def recolor(self, str: color):
        if self.isVisible:
            self.unselectedColor = color
            if not select.isSelected:
                self.zframe.canvas.itemconfig(self.hline, fill=color)
                self.zframe.canvas.itemconfig(self.vline, fill=color)

class MetadataModule:
    def __init__(self, App: app, str: path):
        pass

    def importOldMeasurement(self, str: filepath, filename):
        pass

    def write(self, str: mdfile = None):
        pass # pretty-print JSON to file

    def getFilenames(self):
        pass

    def getPreprocessedDicom(self, int: frame = None):
        try:
            return self.unrelativize($getFrame(frame))
        except:
            return None

    def (get|set)(Top|File)Level(self, value, ?value):
        pass

    def unrelativize(self, str: filename): # lol
        return os.path.join(self.path, filename)

    # lots of other useless methods ...

class TextGridModule:
    def __init__(self, App: app):
        self.app = app
        self.frame = tk.Frame(self.app.BOTTOM)
        self.frame.grid(row=1, column=1)
        self.canvas_frame = tk.Frame(self.app.BOTTOM)
        self.canvas_frame.grid(row=1, column=1)
        self.TextGrid: textgrid.TextGrid = None
        self.selectedTier = tk.StringVar()
        self.frame_shift = DoubleVar()
        # ... and more ...

    def startup(self):
        if _TEXTGRID_LIBS_INSTALLED:
            self.TkWidgets = [{
                'label': tk.Label(self.frame, text='Unable to load TextGrid file' )
            }]
            filename = self.app.Data.getFileLevel('.TextGrid')
            if filename:
                try:
                    self.TextGrid = TextGrid.fromFile(self.app.Data.unrelativize(filename))
                    self.frameTierName = self.getFrameTierName()
                    self.app.frames = len(self.TextGrid.getFirst(self.frameTierName))
                    for tier in self.TextGrid.getNames():
                        if tier != self.frameTierName and tier != f'{self.frameTierName}.original':
                            tierWidgets = self.makeTierWidgets(tier)
                            self.TkWidgets.append(tierWidgets)
                    self.makeFrameWidget()
                    self.makeTimeWidget()
                    self.fillCanvases()
                    self.firstFrame = int(self.TextGrid.getFirst(self.frameTierName)[0].mark) + 1
                    self.startFrame = self.firstFrame
                    self.lastFrame = int(self.TextGrid.getFirst(self.frameTierName)[-1].mark) + 1
                    self.endFrame = self.lastFrame
                except:
                    pass # lol @ error-swallowing
            self.grid()

    def reset(self, tk.Event event = None):
        self.selectedIntvlFrames = []
        self.selectedItem = None
        if _TEXTGRID_LIBS_INSTALLED:
            filename = self.app.Data.getFileLevel('.TextGrid')
            if filename:
                try:
                    self.TextGrid = TextGrid.fromFile(self.app.Data.unrelativize(filename))
                    self.frameTierName = self.getFrameTierName()
                    self.app.frames = len(self.TextGrid.getFirst(self.frameTierName))
                    self.start = self.TextGrid.minTime
                    self.end = self.TextGrid.maxTime
                    self.current = self.TextGrid.getFirst(self.frameTierName)[self.app.frame - 1].time
                    offset = self.app.Data.getFileLevel('offset')
                    if offset != None:
                        self.frame_shift.set(offset)
                    else:
                        self.frame_shift.set(0)
                    self.fillCanvases()
                    self.firstFrame = int(self.TextGrid.getFirst(self.frameTierName)[0].mark) + 1
                    self.startFrame = self.firstFrame
                    self.lastFrame = int(self.TextGrid.getFirst(self.frameTierName)[-1].mark) + 1
                    self.endFrame = self.lastFrame
                except:
                    pass # lol @ error-swallowing

    def shiftFrames(self):
        raise NotImplementedError()

    def makeTimeWidget(self):
        raise NotImplementedError()

    def makeFrameWidget(self):
        raise NotImplementedError()

    def getFrameTierName(self):
        for name in _TEXTGRID_ALIGNMENT_TIER_NAMES:
            if name in self.TextGrid.getNames():
                return name
        raise NameError('Unable to find alignment tier')

    def getClickedFrame(self, tk.Event: event):
        item = self.my_find_closest(event.widget, event.x)
        self.setSelectedIntvlFrames( (event.widget, item) )
        frame = event.widget.gettags(item)[0][5:]
        self.app.frame = int(frame)
        if not frame in self.selectedIntvlFrames:
            self.selectedIntvlFrames = []
            self.wipeFill()
        self.app.framesUpdate()

    def makeTierWidgets(self, Unknown: tier):
        raise NotImplementedError()

    def changeIntervals(self, tk.Event: event):
        raise NotImplementedError()

    def changeTiers(self, tk.Event: event):
        raise NotImplementedError()

    def getMinMaxTime(self):
        start = None
        end = None
        for tag in self.selectedItem[0].gettags(self.selectedItem[1]):
            if tag[:7] == 'minTime':
                start = decimal.Decimal(tag[7:])
            elif tag[:7] == 'maxTime':
                end = decimal.Decimal(tag[7:])
        if start is None:
            start = self.start
        if end is None:
            end = self.end
        return (start, end)

    def getBounds(self, tk.Event: event):
        raise NotImplementedError()

    def getTracedFrames(self, List<Unknown>: frames) -> List<Unknown>:
        frames = [ frame[5:] for frame in frames ]
        tracesFrames = []
        for trace in self.app.Data.data['traces']:
            tracedFrames += self.app.Data.tracesExist(trace)
        return set(frames).intersection(tracedFrames)

    def fillCanvases(self):
        raise NotImplementedError()

    def updateTimeLabels(self):
        raise NotImplementedError()

    def updateTierLabels(self):
        for w in self.TkWidgets:
            if 'canvas' in w:
                current_label = w['canvas-label'].find_all()[0]
                nonempty_frames = w['canvas-label'].gettags(current_label)
                w['canvas-label'].itemconfig(
                        current_label,
                        text=f'{w["name"]}:\n({len(self.getTracedFrames(nonempty_frames))}/{len(nonempty_frames)})')

    def my_find_closest(self, tk.Widget: widget, float: x) -> Unknown:
        raise NotImplementedError()

    def setSelectedIntvlFrames(self, Tuple<tk.Widget, Unknown> tup):
        widget, item = tup
        self.selectedIntvlFrames = []
        for tag in widget.gettags(item):
            if tag[:5] == 'frame':
                self.selectedIntvlFrames.append(x[5:])

    def wipeFill(self):
        raise NotImplementedError()

    def genFrameList(self, tk.Event: event = None, tk.Widget: widget = None, float x: None, Unknown: SI = False):
        raise NotImplementedError()

    def collapse(self, tk.Event: event):
        raise NotImplementedError()

    def painCanvases(self):
        raise NotImplementedError()

    def update(self):
        raise NotImplementedError()

    def grid(self, tk.Event: event = None):
        for i, widgets in enumerate(self.TkWidgets):
            if 'label' in widgets:
                widgets['label'].grid(row=i, column=0, sticky='w')
            if 'frames' in widgets:
                widgets['frames'].grid(row=i, column=2, sticky='w', pady=self.app.pady)
                widgets['frames-label'].grid(row=i, column=0, sticky='w', pady=self.app.pady)
            if 'canvas' in widgets:
                widgets['canvas'].grid(row=i, column=2, sticky='w', pady=(self.app.pady / 2))
                widgets['canvas-label'].grid(row=i, column=0, sticky='w', pady=(self.app.pady / 2))
                self.tier_pars[widgets['canvas-label']] = widgets['canvas']
            if 'times' in widgets:
                widgets['times'].grid(row=i, column=2, sticky='s')

class SpectrogramModule:
    def __init__(self, App: app):
        raise NotImplementedError()
    def doDefaults(self):
        raise NotImplementedError()
    def restoreDefaults(self):
        raise NotImplementedError()
    def update(self):
        raise NotImplementedError()
    def reset(self):
        raise NotImplementedError()
    def drawSpectrogram(self, tk.Event event = None):
        raise NotImplementedError()
    def drawInterval(self):
        raise NotImplementedError()
    def jumpToFrame(self):
        raise NotImplementedError()
    def xToTime(self, float: x) -> float:
        return (x * (self.app.TextGrid.end - self.app.TextGrid.start) / self.canvas_width) + self.app.TextGrid.start
    def timeToX(self, float: time) -> float:
        return self.canvas_width * (time - self.app.TextGrid.start) / (self.app.TextGrid.end - self.app.TextGrid.start)
    def grid(self):
        self.canvas.grid(row=0, column=0, sticky='news')
        self.spinwin.grid(row=0, column=0, sticky='ne')

class TraceModule:
    def __init__(self, App: app):
        self.xhairs: Dict<str,List<XHair>> = {}
        self.selected: Set<XHair> = set()
        raise NotImplementedError()
    def update(self):
        self.reset()
        self.read()
    def reset(self):
        for xhairs in self.xhairs.items():
            for xhair in xhairs:
                xhair.undraw()
        self.xhairs = {}
        self.selected = set()
    def add(self, float: x, float: y, str: trace = None, bool: transform = True) -> XHair:
        raise NotImplementedError()
    def remove(self, XHair: xhair, bool: write = True) -> XHair:
        raise NotImplementedError()
    def move(self):
        raise NotImplementedError()
    def read(self):
        raise NotImplementedError()
    def write(self):
        raise NotImplementedError()
    def getCurrentTraceName(self) -> str:
        try:
            return self.listbox.get(self.listbox.curselection())
        except tk.TclError:
            print("Can't select from empty listbox!")
    def setDefaultTraceName(self):
        self.app.Data.setTopLevel('defaultTraceName', self.getCurrentTraceName())
    def select(self, XHair: xhair):
        xhair.select()
        self.selected.add(xhair)
    def selectAll(self):
        if self.getCurrentTraceName() in self.xhairs:
            for xhair in self.xhairs[self.getCurrentTraceName()]:
                self.select(xhair)
    def unselect(self, XHair: xhair):
        xhair.unselect()
        self.selected.remove(xhair)
    def unselectAll(self):
        for xhair in self.selected:
            xhair.unselect()
        self.selected = set()
    def getNearClickAllTraces(self, Tuple<float,float>: click) -> XHair:
        raise NotImplementedError()
    def getNearClickOneTrace(self, Tuple<float,float>: click, str: trace) -> XHair:
        raise NotImplementedError()
    def copy(self, tk.Event: event = None):
        raise NotImplementedError()
    def paste(self, tk.Event: event = None):
        raise NotImplementedError()
    def recolor(self, tk.Event: event = None, str: trace = None, str: color = None) -> str:
        raise NotImplementedError()
    def clear(self):
        raise NotImplementedError()
    def newTrace(self):
        raise NotImplementedError()
    def renameTrace(self, str: oldName = None, str: newName = None):
        raise NotImplementedError()
    def getRandomHexColor(self) -> str:
        return f'#{random.randint(0, 0xffffff):06x}'
    def getWidget(self,
            Unknown: widget,
            int: row = 0,
            int col = 0,
            int rowspan = 1,
            int columnspan = 1,
            str: sticky = '') -> dict:
        return {
                'widget': widget,
                'row': row,
                'rowspan': rowspan,
                'column': column,
                'columnspan': columnspan,
                'sticky': sticky }
    def grid(self):
        for widget in self.TkWidgets:
            item['widget'].grid(
                    row=item['row'],
                    column=item['column'],
                    rowspan=item['rowspan'],
                    columnspan=item['columnspan'],
                    sticky=item['sticky'])
        self.listbox.pack(side=LEFT, fill=Y)
        self.scrollbar.pack(side=RIGHT, fill=Y)
    def grid_remove(self):
        for item in self.TkWidgets:
            item['widget'].grid_remove()
        self.listbox.packforget()
        self.scrollbar.packforget()

class PlaybackModule:
    def __init__(self, App: app):
        raise NotImplementedError()
    def update(self):
        pass
    def reset(self):
        raise NotImplementedError()
    def loadAudio(self, str: codec) -> bool:
        raise NotImplementedError()
    def playpauseAV(self, tk.Event event):
        raise NotImplementedError()
    def readyAudio(self, int: start, int: end):
        raise NotImplementedError()
    def readyVideo(self):
        raise NotImplementedError()
    def callback(self, Unknown: _data, int: frame_count, Unknown: _time_info, Unknown: _status) -> Tuple<Unknown, pyaudio.paContinue>:
        raise NotImplementedError()
    def playAudio(self):
        self.stream.start_stream()
        self.started = True
        if self.app.Dicom.isLoaded:
            self.playVideoWithAudio()
        else:
            pass # FIXME?
        if self.stoprequest.is_set():
            self.stopAV()
    def playVideoWithAudio(self):
        raise NotImplementedError()
    def playVideoNoAudio(self):
        raise NotImplementedError()
    def stopAV(self, tk.Event: event = None):
        raise NotImplementedError()
    def grid(self):
        self.frame.grid(row=0)
        self.playBtn.grid()
    def ungrid(self):
        self.frame.grid_remove()
        self.playBtn.grid_remove()

class DicomModule:
    def __init__(self, App: app):
        raise NotImplementedError()
    def zoomReset(self, bool fromButton = False):
        raise NotImplementedError()
    def update(self, int: frame = None):
        raise NotImplementedError()
    def load(self, tk.Event: event = None):
        raise NotImplementedError()
    def process(self):
        # perform the dicom -> PNG conversion
        raise NotImplementedError()
    def reset(self):
        raise NotImplementedError()
    def grid(self):
        self.app.framesHeader.grid(row=0)
        self.app.framesPrevBtn.grid(row=0, column=0)
        self.app.framesEntryText.grid(row=0, column=1)
        self.app.framesEntryBtn.grid(row=0, column=2)
        self.app.framesNextBtn.grid(row=0, column=3)
        self.zoomResetBtn.grid(row=7)
        self.app.Control.grid()
    def grid_remove(self):
        self.app.framesHeader.grid_remove()
        self.app.framesPrevBtn.grid_remove()
        self.app.framesEntryText.grid_remove()
        self.app.framesEntryBtn.grid_remove()
        self.app.framesNextBtn.grid_remove()
        self.zoomResetBtn.grid_remove()
        self.app.Control.grid_remove()

class ControlModule:
    # ... stuff to control undo/redo ...
    def grid(self):
        self.undoBtn.grid(row=0, column=0)
        self.redoBtn.grid(row=0, column=1)
    def grid_remove(self):
        self.undoBtn.grid_remove()
        self.redoBtn.grid_remove()

class App(ThemedTk):
    def __init__(self):
        super().__init__() # w/ or w/o theme
        self.Data = MetadataModule(self, args.path) # from argparse
        self.setWidgetDefaults()
        self.buildWidgetSkeleton()

        self.Control = ControlModule(self)
        self.Trace = TraceModule(self)
        self.Dicom = DicomModule(self)
        self.Audio = PlaybackModule(self)
        self.TextGrid = TextGridModule(self)
        self.Spectrogram = SpectrogramModule(self)

        self.filesUpdate()

        self.isResizing = False
        self.after(300, self.afterstartup)

    def setWidgetDefaults(self):
        self.currentFID = 0
        self.frame = 0
        self.isClicked = False
        self.isDragging = False
        self.selectBoxX = False
        self.selectBoxY = False
        self.currentFileSV = StringVar(self)
        self.frameSV = StringVar(self)
        self.currentFileSV.set(self.Data.files[self.currentFID])
        self.frameSV.set('1')

    def buildWidgetSkeleton(self):
        # main Frame skeleton
        self.TOP = Frame(self)
        self.TOP.columnconfigure(1,weight=1, minsize=320)
        self.TOP.rowconfigure(0,weight=1, minsize=240)
        self.LEFT = Frame(self.TOP)
        self.RIGHT = Frame(self.TOP)
        self.RIGHT.rowconfigure(0,weight=1)
        self.RIGHT.columnconfigure(0,weight=1)
        self.BOTTOM = Frame(self)
        self.BOTTOM.columnconfigure(1,weight=1)
        self.TOP.grid(    row=0, column=0, sticky=N+E+S+W)
        self.LEFT.grid(   row=0, sticky=N+E+S+W )
        self.RIGHT.grid(  row=0, column=1, sticky=N+E+S+W)
        self.BOTTOM.grid( row=1, column=0, sticky=N+E+S+W)
        self.pady=3
        self.columnconfigure(0,weight=1)
        self.rowconfigure(0,weight=1)

        # navigate between all available filenames in this directory
        self.filesFrame = Frame(self.LEFT)#, pady=7)
        self.filesPrevBtn = Button(self.filesFrame, text='<', command=self.filesPrev, takefocus=0)
        self.filesJumpToMenu = OptionMenu(self.filesFrame, self.currentFileSV, *self.Data.files, command=self.filesJumpTo)
        self.filesNextBtn= Button(self.filesFrame, text='>', command=self.filesNext, takefocus=0)
        self.filesPrevBtn.grid( row=1, column=0 )
        self.filesFrame.grid( row=1 )
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
        self.bind('<Option-Left>', self.filesPrev )
        self.bind('<Option-Right>', self.filesNext )
        self.bind('<Left>', self.framesPrev )
        self.bind('<Right>', self.framesNext )
        self.bind('<BackSpace>', self.onBackspace )
        self.bind('<Button-1>', self.getWinSize)
        self.bind('<ButtonRelease-1>', self.onRelease)
        self.bind('<Double-Button-1>', self.onDoubleClick)
        self.bind('<Escape>', self.onEscape )

        self.framesEntryText.bind('<Return>', self.unfocusAndJump)
        self.framesEntryText.bind('<Escape>', lambda ev: self.framesFrame.focus())

        # force window to front
        self.attributes('-topmost', 1)
        self.attributes('-topmost', 0)

    def afterstartup(self):
        self.bind('<Configure>', self.alignBottomLeftWrapper)
        self.alignBottomLeft()
        self.getWinSize()
        self.alignBottomRight(self.oldwidth - self.leftwidth)
        if self.Dicom.zframe.image:
            self.Dicom.zframe.setImage(self.Dicom.zframe.image)

    def alignBottomLeftWrapper(self, tk.Event: event = None):
        if self.isResizing:
            return
        self.isResizing = True
        self.after(100, lambda: self.alignBottomLeft(event))

    def alignBottomLeft(self, tk.Event: event = None):
        raise NotImplementedError()

    def alignBottomRight(self, float: x):
        raise NotImplementedError()

    def getWinSize(self, tk.Event: event = None):
        self.oldwidth = self.winfo_width()

    def onDoubleClick(self, tk.Event: event):
        nearby = self.Trace.getNearClickAllTraces( (event.x, event.y) )
        if nearby != None:
            self.Trace.unselectAll()
            self.Trace.select(nearby)

    def onClickZoom(self, event):
        raise NotImplementedError()

    def onReleaseZoom(self, event):
        raise NotImplementedError()

    def onReleaseSpec(self, event):
        raise NotImplementedError()

    def onRelease(self, event):
        raise NotImplementedError()

    def onMotion(self, event):
        raise NotImplementedError()

    def onEscape(self, event):
        self.isDragging = False
        self.isClicked = False
        self.Trace.unselectAll()

    def onBackspace(self, event):
        for xhair in self.Trace.selected:
            self.Trace.remove(xhair)
        self.Control.push({
            'type': 'delete',
            'xhairs': self.Trace.selected
        })
        self.Trace.unselectAll()

    def filesUpdate(self):
        self.currentFileSV.set(self.Data.files[self.currentFID])
        self.frame = 1
        self.frames = 1

        self.Control.reset()
        self.Trace.reset()
        self.Dicom.reset()
        self.Audio.reset()
        self.TextGrid.reset()
        self.Spectrogram.reset()

        #self.filesPrevBtn['state'] = (expr) ? NORMAL : DISABLED
        #self.filesNextBtn['state'] = (expr) ? NORMAL : DISABLED

        self.framesUpdate()

    def framesUpdate(self):
        self.frameSV.set(str(self.frame))
        self.Control.update()
        self.Dicom.update()
        self.Trace.update()
        self.Audio.update()
        self.TextGrid.update()
        self.Spectrogram.update()
        #self.framesPrevBtn['state'] = (expr) ? NORMAL : DISABLED
        #self.framesNextBtn['state'] = (expr) ? NORMAL : DISABLED

    def filesPrev(self):
        if self.Data.getFileLevel('_prev') is not None:
            self.currentFID -= 1
            self.filesUpdate()
    def filesNext(self):
        if self.Data.getFileLevel('_next') is not None:
            self.currentFID += 1
            self.filesUpdate()
    def filesJumpTo(self, choice):
        self.currentFID = self.Data.files.index(choice)
        self.filesUpdate()

    def framesPrev(self):
        if isinstance(self.focus_get(), (Entry, Spinbox)):
            return
        if self.frame > self.TextGrid.startFrame:
            self.frame -= 1
            self.framesUpdate()
    def framesNext(self):
        if isinstance(self.focus_get(), (Entry, Spinbox)):
            return
        if self.frame < self.TextGrid.endFrame:
            self.frame += 1
            self.framesUpdate()
    def framesJumpTo(self):
        try:
            choice = int(self.frameSV.get())
            if choice < 1:
                self.frame = 1
            elif choice > self.frames:
                self.frame = self.frames
            else:
                self.frame = choice
            self.framesUpdate()
        except ValueError:
            print('Please enter an integer!')

class CanvasTooltip:
    raise NotImplementedError()

def printProgressBar(*args, **kwargs):
    raise NotImplementedError()

