from .base import Module
from .. import util
from ..util.logging import *
from ..widgets import CanvasTooltip
import copy

from tkinter.ttk import Button, Frame, Label
from tkinter import Canvas, StringVar, DoubleVar
try:
    # ttk.Spinbox was added in Python 3.7
    from tkinter.ttk import Spinbox
except ImportError:
    from tkinter import Spinbox
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
        info( ' - initializing module: TextGrid' )
        self.app = app
        self.frame = Frame(self.app.BOTTOM)
        self.label_padx = 0
        self.canvas_frame = Frame(self.app.BOTTOM)#, padx=self.label_padx)
        self.frame.grid( row=1, column=0, sticky='ne')
        self.canvas_frame.grid(row=1, column=1 )
        self.TextGrid = None
        self.selectedTier = StringVar()
        self.tg_zoom_factor = 1.5
        self.canvas_width=800
        self.canvas_height=60
        self.collapse_height=15
        self.selectedIntvlFrames = []
        self.selectedItem = None
        self.start = 0
        self.end = 0
        self.current = 0
        self.frame_shift = DoubleVar()

        self.startup()

        platform = util.get_platform()
        #bindings
        if platform == 'Linux':
            self.app.bind("<Control-n>", self.getBounds)
            self.app.bind("<Control-a>", self.getBounds)
            self.app.bind("<Control-i>", self.getBounds)
            self.app.bind("<Control-o>", self.getBounds)
            self.app.bind("<Control-f>", self.openSearch)
            # Command is Alt in Linux, apparently
            self.app.bind("<Command-Up>", self.changeTiers)
            self.app.bind("<Command-Down>", self.changeTiers)
            self.app.bind("<Command-Left>", self.changeIntervals)
            self.app.bind("<Command-Right>", self.changeIntervals)
        elif platform == 'Darwin':
            self.app.bind("<Command-n>", self.getBounds)
            self.app.bind("<Command-a>", self.getBounds)
            self.app.bind("<Command-i>", self.getBounds)
            self.app.bind("<Command-o>", self.getBounds)
            self.app.bind("<Command-f>", self.openSearch)
            self.app.bind("<Option-Up>", self.changeTiers)
            self.app.bind("<Option-Down>", self.changeTiers)
            self.app.bind("<Option-Left>", self.changeIntervals)
            self.app.bind("<Option-Right>", self.changeIntervals)
        #defaults (Command/Alt everything)
        else:
            self.app.bind("<Command-n>", self.getBounds)
            self.app.bind("<Command-a>", self.getBounds)
            self.app.bind("<Command-i>", self.getBounds)
            self.app.bind("<Command-o>", self.getBounds)
            self.app.bind("<Command-f>", self.openSearch)
            self.app.bind("<Command-Up>", self.changeTiers)
            self.app.bind("<Command-Down>", self.changeTiers)
            self.app.bind("<Command-Left>", self.changeIntervals)
            self.app.bind("<Command-Right>", self.changeIntervals)

        # these aren't Praat-like
        self.app.bind("<Shift-Left>", self.getBounds)
        self.app.bind("<Shift-Right>", self.getBounds)


    def setup(self):
        if LIBS_INSTALLED:
            self.loadOrGenerate()
            try:
                self.start = self.TextGrid.minTime
                self.end = self.TextGrid.maxTime
                self.app.frames = len(self.TextGrid.getFirst(self.frameTierName))
                tiers = []
                for tier in self.TextGrid.getNames():
                    if tier != self.frameTierName and tier != self.frameTierName + '.original':
                        tiers.append(tier)
                if set(tiers) != self.tierNames:
                    self.tierNames = set(tiers)
                    self.TkWidgets = []
                    for label in self.frame.winfo_children():
                        label.destroy()
                    for canvas in self.canvas_frame.winfo_children():
                        canvas.destroy()
                    for tier in self.TextGrid.getNames():
                        if tier != self.frameTierName and tier != self.frameTierName + '.original':
                            self.TkWidgets.append(self.makeTierWidgets(tier))
                    self.makeFrameWidget()
                    self.makeTimeWidget()
                self.fillCanvases()
                self.firstFrame = int(self.TextGrid.getFirst(self.frameTierName)[0].mark) + 1
                self.startFrame = self.firstFrame
                self.lastFrame = int(self.TextGrid.getFirst(self.frameTierName)[-1].mark) + 1
                self.endFrame = self.lastFrame
                self.grid()
            except Exception as e:
                error(e)



    def startup(self):
        '''

        '''
        if LIBS_INSTALLED:
            self.tierNames = set()
            self.setup()

    def reset(self, event=None):
        '''
        Try to load a TextGrid file based on information stored in the metadata
        '''
        if LIBS_INSTALLED:
            self.selectedIntvlFrames = []
            self.selectedItem = None
            self.setup()

    def fromFile(self, filename):
        if LIBS_INSTALLED:
            try:
                return TextGridFile.fromFile(filename)
            except (TextGridError, UnicodeDecodeError) as e:
                f = open(filename, 'rb')
                contents = util.decode_bytes(f.read())
                f.close()
                if contents:
                    tmp = tempfile.NamedTemporaryFile()
                    tmp.write(contents.encode('utf-8'))
                    tmp.seek(0)
                    try:
                        return TextGridFile.fromFile(tmp.name)
                    except TextGridError as e:
                        error(e)
                        return None
                else:
                    error("can't load from file: unable to decode non-Unicode textgrid", filename)
        else:
            error("can't load from file: textgrid lib not installed")
            return None

    def loadOrGenerate(self):
        fname = self.app.Data.checkFileLevel('.TextGrid', shoulderror=False)
        if fname:
            self.TextGrid = self.fromFile(fname)
        else:
            minTime = 0.
            if not hasattr(self.app.Audio, 'duration'):
                self.app.Audio.reset()
            try:
                maxTime = self.app.Audio.duration
            except:
                warn('Audio has no duration attribute after calling reset(), defaulting to 1 second')
                maxTime = 1.
            self.TextGrid = TextGridFile(maxTime=maxTime)
            keys = self.app.Data.getFileLevel('all')
            if not ('.ult' in keys and '.txt' in keys):
                sentenceTier = IntervalTier("text")
                sentenceTier.add(minTime, maxTime, "text")
                self.TextGrid.append(sentenceTier)
            fname = self.app.Data.unrelativize(self.app.Data.getCurrentFilename() + '.TextGrid')
            self.app.Data.setFileLevel('.TextGrid', fname)
        names = self.TextGrid.getNames()
        for i, n in enumerate(names):
            if n in ALIGNMENT_TIER_NAMES:
                if len(self.TextGrid[i]) == 0:
                    self.TextGrid.pop(i)
                    break
                else:
                    self.frameTierName = n
                    return
        self.genFramesTier()

    def genFramesTier(self):
        debug('generating frames tier for %s' % self.app.Data.getCurrentFilename())
        self.frameTierName = 'frames'
        times = self.app.Dicom.getFrameTimes()
        self.app.Data.setFileLevel("NumberOfFrames", len(times))
        try:
            maxTime = max(self.app.Audio.duration, times[-1])
        except AttributeError:
            maxTime = times[-1]
        tier = PointTier('frames', maxTime=maxTime)
        for f, t in enumerate(times):
            tier.addPoint(Point(t, str(f)))
        if not self.TextGrid.maxTime or maxTime > self.TextGrid.maxTime:
            self.TextGrid.maxTime = maxTime
        self.TextGrid.append(tier)

        keys = self.app.Data.getFileLevel('all')
        if '.ult' in keys and '.txt' in keys:
            fname = self.app.Data.unrelativize(self.app.Data.getFileLevel('.txt'))
            f = open(fname, 'rb')
            s = util.decode_bytes(f.read())
            f.close()
            if s:
                line = s.splitlines()[0]
                sentenceTier = IntervalTier("sentence")
                sentenceTier.add(0, self.app.Audio.duration, line)
                self.TextGrid.append(sentenceTier)
                self.TextGrid.tiers = [self.TextGrid.tiers[-1]] + self.TextGrid.tiers[:-1]
                

        path = self.app.Data.unrelativize(self.app.Data.getFileLevel( '.TextGrid' ))
        self.TextGrid.write(path)
        self.TextGrid = TextGridFile.fromFile(path)
        # reload to account for length changes due to frames tier being different length than audio

    @staticmethod
    def isIntervalTier(tier):
        if LIBS_INSTALLED:
            return isinstance(tier, IntervalTier)
        else:
            error("can't check if IntervalTier: textgrid lib not installed")
            return False

    def shiftFrames(self):
        '''
        Replicate original TextGrid point tier (renamed [tiername].original)
        Shift points on TextGrid tier in accordance with self.frame_shift
            Shift value is relative to 0, i.e. inputting the same shift amount a second time will not change the shift
        Redisplay shifted points
        '''
        self.app.focus()
        shift = self.frame_shift.get()
        if type(shift) == float:
            self.app.Data.setFileLevel( 'offset', shift )
            # diff = shift - self.app.Data.data['offset']
            originalTier = self.TextGrid.getFirst(self.frameTierName+'.original')
            if originalTier: pass
            else:
                orig = copy.deepcopy(self.TextGrid.getFirst(self.frameTierName))
                orig.name += '.original'
                self.TextGrid.append(orig)
                originalTier = self.TextGrid.getFirst(self.frameTierName+'.original')

            oldTier = self.TextGrid.getFirst(self.frameTierName)
            allPoints = oldTier[:]
            for point in allPoints:
                oldTier.removePoint(point)

            for point in originalTier:
                new_time = point.time + shift/1000 ## NOTE: currently in ms
                if self.TextGrid.minTime <= new_time <= self.TextGrid.maxTime:
                    self.TextGrid.getFirst(self.frameTierName).add(new_time, point.mark)

            # self.app.frames = len(self.TextGrid.getFirst(self.frameTierName))         #FIXME I feel like I shouldn't have to run the getFirst function every time, but I'm not sure when I have to go back to the original textgrid, and when I can just use a variable...
            self.firstFrame = int(self.TextGrid.getFirst(self.frameTierName)[0].mark) + 1
            self.lastFrame = int(self.TextGrid.getFirst(self.frameTierName)[-1].mark) + 1
            self.app.Data.data['offset'] = shift
            # self.frame_shift.set(shift)
            self.app.Data.write()
            # newTier.write(self.TextGrid.getFirst(self.frameTierName))
            self.fillCanvases()
            self.TextGrid.write(self.app.Data.unrelativize(self.app.Data.getFileLevel( '.TextGrid' )))


        #except ValueError:
        else:
            error('Not a float!')

    def makeTimeWidget(self):
        self.time_canvas = Canvas(self.canvas_frame, width=self.canvas_width, height=self.canvas_height/3, highlightthickness=0)
        s = self.time_canvas.create_text(3,0, anchor='nw', text=self.start)
        e = self.time_canvas.create_text(self.canvas_width,0, anchor='ne', text=self.end)
        c = self.time_canvas.create_text(self.canvas_width/2,0, anchor='n', text=self.current)
        self.TkWidgets.append({'times':self.time_canvas})

    def makeFrameWidget(self):
        '''
        makes frame widget
        '''
        #make regular frame stuff -- label and tier
        self.frames_canvas = Canvas(self.canvas_frame, width=self.canvas_width, height=self.canvas_height, background='gray', highlightthickness=0)
        frames_label = Canvas(self.frame, width=self.label_width, height=self.canvas_height, highlightthickness=0, background='gray')
        frames_label.create_text(self.label_width,0, anchor='ne', justify='center',
                                 text='frames: ', width=self.label_width, activefill='blue')

        # make subframe to go on top of label canvas
        sbframe = Frame(frames_label)
        #put new widgets onto subframe
        offset = self.app.Data.getFileLevel( 'offset' )
        if offset != None:
            self.frame_shift.set(offset)
        # for audio alignment
        go_btn = Button(sbframe, text='Offset', command=self.shiftFrames, takefocus=0)
        # minmax = len(self.app.Audio.sfile)*1000
        txtbox = Spinbox(sbframe, textvariable=self.frame_shift, width=7, from_=-10000000, to=10000000)
        txtbox.bind('<Escape>', lambda ev: sbframe.focus())
        txtbox.bind('<Return>', lambda ev: self.shiftFrames())
        go_btn.grid(row=0, column=0, sticky='e')
        txtbox.grid(row=0, column=1, sticky='e')
        # put subframe on canvas
        window = frames_label.create_window(self.label_width*.3,self.canvas_height/3, anchor='nw', window=sbframe)
        # ensure position of subframe gets updated
        frames_label.bind('<Configure>', lambda e: frames_label.itemconfig(window, width=e.width))
        sbframe.bind('<Configure>', lambda e: frames_label.configure(scrollregion=frames_label.bbox("all")))

        self.TkWidgets.append({'name':self.frameTierName,'frames':self.frames_canvas,
                               'frames-label':frames_label})

        self.frames_canvas.bind("<Button-1>", self.getClickedFrame)

    def getFrameTierName(self):
        '''
        Handle some inconsistency in how we're naming our alignment tier
        '''
        for name in ALIGNMENT_TIER_NAMES:
            if name in self.TextGrid.getNames():
                return name
        raise NameError( 'Unable to find alignment tier' )

    def getClickedFrame(self, event):
        '''
        Jumps to clicked frame
        '''
        item = self.my_find_closest(event.widget, event.x)
        self.setSelectedIntvlFrames((event.widget, item))
        frame = event.widget.gettags(item)[0][5:]
        self.app.frame = int(frame)
        if not frame in self.selectedIntvlFrames:
            self.selectedIntvlFrames = []
            self.wipeFill()
        self.app.framesUpdate()

    def makeTierWidgets(self, tier):
        '''
        Each tier should have two canvas widgets: `canvas-label` (the tier name),
        and `canvas` (the intervals on the tier with their marks)
        '''
        self.tier_pairs = {} #ends up being format {label: canvas}

        # self.app.Trace.frame.update()
        self.label_width=300#self.app.Trace.frame.winfo_width()+self.label_padx
        self.end = self.TextGrid.maxTime#float(self.TextGrid.maxTime)
        # self.first_frame = 1
        # self.last_frame = self.TextGrid.getFirst(self.frameTierName)[-1].mark
        tier_obj = self.TextGrid.getFirst(tier)
        widgets = { 'name':tier,
                         #'label':Label(self.frame, text=('- '+tier+':'), wraplength=200, justify='left'),
                         'canvas-label':Canvas(self.frame, width=self.label_width, height=self.canvas_height, highlightthickness=0),
                         # 'text' :Label(self.frame, text='', wraplength=550, justify='left'),
                         'canvas':Canvas(self.canvas_frame, width=self.canvas_width, height=self.canvas_height, background='gray', highlightthickness=0)}

        canvas = widgets['canvas']
        label = widgets['canvas-label']

        #builds tier label functionality
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

        return widgets

    def changeIntervals(self,event):
        '''

        '''
        if self.selectedItem:
            duration = self.end - self.start

            # There might be a more efficient way to get the tier name:
            widg = self.selectedItem[0]
            itm = self.selectedItem[1]
            for el in self.TkWidgets:
                if widg in el.values():
                    tier_name = el['name']
                    break

            #finding Interval mintime and maxtime
            oldMinTime = None
            oldMaxTime = None
            q=0
            tags = widg.gettags(itm)
            while oldMinTime == None or oldMaxTime == None:
                if tags[q][:7] == 'minTime':
                    oldMinTime = float(tags[q][7:])
                elif tags[q][:7] == 'maxTime':
                    oldMaxTime = float(tags[q][7:])
                q+=1

            tier = self.TextGrid.getFirst(tier_name)
            intvl_i = tier.indexContaining(oldMaxTime-((oldMaxTime-oldMinTime)/2))

            if event.keysym == 'Left':
                new_intvl_i = intvl_i-1
            elif event.keysym == 'Right':
                new_intvl_i = intvl_i+1
            if 0 <= new_intvl_i < len(tier):
                #find characteristics of new adjacent interval
                newMinTime = tier[new_intvl_i].minTime
                newMaxTime = tier[new_intvl_i].maxTime
                itvlDuration = newMaxTime - newMinTime
                newCenter = newMinTime + itvlDuration/2

                #figure out new window parameters based on new interval
                start = newCenter - duration/2
                end = newCenter + duration/2
                if start < 0:
                    self.start = 0
                    self.end = duration
                elif end > self.TextGrid.maxTime:
                    self.start = self.TextGrid.maxTime - duration
                    self.end = self.TextGrid.maxTime
                else:
                    self.start = newCenter - duration/2
                    self.end = newCenter + duration/2
                relDuration = self.end - self.start

                # select new item
                rel_time = newCenter - self.start
                x_loc = float(rel_time/relDuration*self.canvas_width)
                item = self.my_find_closest(widg, x_loc)
                self.selectedItem = (widg, item)
                self.setSelectedIntvlFrames(self.selectedItem)

                self.fillCanvases()
                self.genFrameList(widg=widg, x_loc=x_loc)

    def changeTiers(self, event):
        '''

        '''
        index = None
        if self.selectedItem:
            for i, el in enumerate(self.TkWidgets):
                if self.selectedItem[0] in el.values():
                    index = i

            if index != None:
                if event.keysym == 'Up' and 'canvas' in self.TkWidgets[index-1]:
                    new_widg = self.TkWidgets[index-1]['canvas']
                elif event.keysym == 'Down' and 'canvas' in self.TkWidgets[index+1]:
                    new_widg = self.TkWidgets[index+1]['canvas']
                else:
                    return

                new_item = new_widg.find_withtag("frame"+str(self.app.frame))[0]
                self.selectedItem = (new_widg, new_item)

                self.fillCanvases()
                self.update()
                self.app.Spectrogram.update()

    def getMinMaxTime(self):
        '''
        Returns minTime and maxTime tags from selected interval
        If no minTime or maxTime, returns start or end time of viewed section of TextGrid
        '''
        start=None
        end=None

        for tag in self.selectedItem[0].gettags(self.selectedItem[1]):
            if tag[:7] == 'minTime':
                start = float(tag[7:])
            elif tag[:7] == 'maxTime':
                end = float(tag[7:])

        if start==None:
            start=self.start
        if end==None:
            end=self.end

        return (start,end)

    def getBounds(self, event):
        '''

        '''
        # debug(event.char, event.keysym, event.keycode)
        # debug(self.app.frame)
        f = self.tg_zoom_factor
        a = self.end - self.start
        z_out = (a-(a/f))/2
        z_in = ((f*a)-a)/2
        old_start = self.start
        old_end = self.end

        if event.keysym == 'n':
            if self.selectedItem:
                self.start, self.end = self.getMinMaxTime()
            # for tag in self.selectedItem[0].gettags(self.selectedItem[1]):
            #   if tag[:7] == 'minTime':
            #       self.start = float(tag[7:])
            #   elif tag[:7] == 'maxTime':
            #       self.end = float(tag[7:])
        if event.keysym == 'a':
            self.start = 0
            self.end = self.TextGrid.maxTime
        if event.keysym == 'o':
            self.start = self.start - z_in
            self.end = self.end + z_in
        if event.keysym == 'i':
            self.start = self.start + z_out
            self.end = self.end - z_out
        if event.keysym == 'Left':
            start = self.start - a/(10*f)
            end = self.end - a/(10*f)
            if (start < 0):
                self.start = 0
                self.end = a
            else:
                self.start = start
                self.end = end
        if event.keysym == 'Right':
            start = self.start + a/(10*f)
            end = self.end + a/(10*f)
            if end > self.TextGrid.maxTime:
                self.start = self.TextGrid.maxTime - a
                self.end = self.TextGrid.maxTime
            else:
                self.start = start
                self.end = end

        self.fillCanvases()

    def getTracedFrames(self,frames):
        '''

        '''
        frames = [frame[5:] for frame in frames] #to get rid of word "frame in tag"
        tracedFrames = []
        for trace in self.app.Data.data['traces']:
            tracedFrames = tracedFrames+self.app.Data.tracesExist(trace)

        return set(frames).intersection(tracedFrames)

    def fillCanvases(self):
        '''

        '''
        if self.start < 0:
            self.start = 0.
        if self.end > self.TextGrid.maxTime:
            self.end = self.TextGrid.maxTime
        self.updateTimeLabels()

        if self.selectedItem:
            old_selected_tags = self.selectedItem[0].gettags(self.selectedItem[1])
        duration = self.end - self.start
        self.frameTier = self.TextGrid.getFirst(self.frameTierName)
        for el in self.TkWidgets:
            if 'name' in el:
                tier = self.TextGrid.getFirst(el['name'])
                # debug(tier)
            if 'canvas' in el:
                canvas = el['canvas']
                #remove previous intervals
                canvas.delete('all')
                #get starting interval
                i = tier.indexContaining(self.start)
                # not sure why, but this is sometimes None -JNW 2020-01-28
                if i != None:
                    #debug(self.TextGrid, self.current, el, tier, self.start, i)
                    time = tier[i].maxTime
                    frame_i = 0
                    while i < len(tier) and tier[i].minTime <= self.end:
                        if self.start >= tier[i].minTime:
                            strtime = self.start
                        else:
                            strtime = tier[i].minTime
                        if self.end <= tier[i].maxTime:
                            time = self.end
                        length = time - strtime
                        pixel_length = length/duration*self.canvas_width

                        mod = length/2
                        rel_time = time-self.start
                        loc=(rel_time-mod)/duration*self.canvas_width

                        text = canvas.create_text(loc, self.canvas_height/2, justify='center',
                                            text=tier[i].mark, width=pixel_length, activefill='blue')
                        minTimetag = "minTime"+str(tier[i].minTime)
                        maxTimetag = "maxTime"+str(tier[i].maxTime)
                        canvas.addtag_withtag(minTimetag, text)
                        canvas.addtag_withtag(maxTimetag, text)
                        #add containted frames to tags
                        while frame_i < len(self.frameTier) and self.frameTier[frame_i].time <= tier[i].maxTime:
                            if self.frameTier[frame_i].time >= tier[i].minTime:
                                canvas.addtag_withtag("frame"+self.frameTier[frame_i].mark, text)
                                if tier[i].mark != '':
                                    el['canvas-label'].addtag_all("frame"+self.frameTier[frame_i].mark)
                            frame_i+=1
                        #pass on selected-ness
                        if self.selectedItem:
                            if self.selectedItem[0] != self.app.Spectrogram.canvas:
                                # old_selected_tags = self.selectedItem[0].gettags(self.selectedItem[1])
                                if minTimetag in old_selected_tags and maxTimetag in old_selected_tags and canvas == self.selectedItem[0]:
                                    # I'm not sure why, but when collapsing canvases this sometimes
                                    # changes which tier is selected. Adding canvas == self.selectedItem[0]
                                    # seems to fix this though.
                                    # - D.S. 2020-01-30
                                    self.selectedItem = (canvas, text)
                        #create line
                        loc=rel_time/duration*self.canvas_width
                        i+=1
                        if i < len(tier) and loc < self.canvas_width:
                            canvas.create_line(loc,0,loc,self.canvas_height, tags='line')
                            time = tier[i].maxTime #here so that loop doesn't run an extra time

                    #fills labels with info about tiers w/traces
                    self.updateTierLabels()

            elif 'frames' in el:
                frames = el['frames']
                i = 0
                frames.delete('all')
                first_frame_found = False
                while i < len(tier) and tier[i].time <= self.end :
                    # debug(tier[i].time, i,'frame time and frame number (line 1076)')
                    if tier[i].time >= self.start:
                        # x_coord = (tier[i].time-self.start)/duration*self.canvas_width
                        x_coord = ((tier[i].time-self.start)*self.canvas_width)/duration
                        #determine fill
                        if tier[i].mark in self.app.Data.getCurrentTraceTracedFrames():
                            fill = 'black'
                        else:
                            fill = 'gray70'
                        frame = frames.create_line(x_coord, 0, x_coord, self.canvas_height, tags="frame"+tier[i].mark, fill=fill)
                        if first_frame_found == False and i + 1 < len(tier):
                            self.firstFrame = int(tier[i].mark) + 1
                            first_frame_found = True
                            self.frame_len = tier[i+1].time - tier[i].time
                        CanvasTooltip(frames, frame,text=tier[i].mark)
                    i+=1
                self.lastFrame = int(tier[i-1].mark)

        self.paintCanvases()
        if hasattr(self.app, 'Spectrogram'):
            # don't try to call this during startup
            # because TextGrid is loaded earlier
            self.app.Spectrogram.reset()

    def updateTimeLabels(self):
        '''

        '''
        self.current = self.TextGrid.getFirst(self.frameTierName)[self.app.frame-1].time
        self.TkWidgets[-1]['times'].itemconfig(1,text='{:.6f}'.format(self.start))
        self.TkWidgets[-1]['times'].itemconfig(2,text='{:.6f}'.format(self.end))
        self.TkWidgets[-1]['times'].itemconfig(3,text='{:.6f}'.format(self.current))

    def updateTierLabels(self):
        '''

        '''
        for el in self.TkWidgets:
            if 'canvas' in el:
                current_label = el['canvas-label'].find_all()[0]
                nonempty_frames = el['canvas-label'].gettags(current_label)
                el['canvas-label'].itemconfig(current_label,
                  text='{}:\n({}/{})'.format(el['name'],len(self.getTracedFrames(nonempty_frames)), len(nonempty_frames)))


    def my_find_closest(self, widg, x_loc):
        '''
        replaces TkInter's find_closest function, which is buggy, determines
        whether found item is text, line, or label, and returns corresponding item
        '''
        #could be more efficient FIXME
        maybe_item = None
        dist = 999999999999
        for el in widg.find_all():
            obj_x = widg.coords(el)[0]
            if abs(obj_x-x_loc) < dist:
                dist = abs(obj_x-x_loc)
                maybe_item = el

        if widg in self.tier_pairs.keys(): #on tier-label canvas
            #fill selected tier frames
            # self.setSelectedIntvlFrames(widg,item)
            item = maybe_item

        elif widg in self.tier_pairs.values(): #on canvas with intervals/frames
            if isinstance(maybe_item, int):
                # #if item found is a boundary
                # if len(widg.gettags(maybe_item)) == 0 or widg.gettags(maybe_item) == ('current',):
                if 'line' in widg.gettags(maybe_item):
                    #determine on which side of the line the event occurred
                    if widg.coords(maybe_item)[0] > x_loc:
                        item = maybe_item-1
                    else: #i.e. event was on line or to the right of it
                        item = maybe_item+1
                else:
                    item = maybe_item

                # self.setSelectedIntvlFrames(widg,item)
        else:
            item = maybe_item

        return item
    def setSelectedIntvlFrames(self,tupl):
        ''' '''
        widg,item=tupl
        self.selectedIntvlFrames = []
        for x in widg.gettags(item):
            if x[:5] == 'frame':
                self.selectedIntvlFrames.append(x[5:])

    def wipeFill(self):
        '''
        Turns selected frame and interval back to black
        '''
        for frame in range(1,self.app.frames+1):
            if str(frame) in self.app.Data.getCurrentTraceTracedFrames():
                fill = 'black'
            else:
                fill = 'gray70'
            self.frames_canvas.itemconfig('frame'+str(frame), fill=fill)
        if self.selectedItem:
            wdg,itm = self.selectedItem
            if wdg.type(itm) != 'text' and wdg.type(itm) != None:
                wdg,itm = self.app.Spectrogram.oldSelected
            wdg.itemconfig(itm, fill='black')
            if len(wdg.find_withtag(itm+1)) > 0:
                wdg.itemconfig(itm+1, fill='black')
            if len(wdg.find_withtag(itm-1)) > 0:
                wdg.itemconfig(itm-1, fill='black')
            #clicked tier label
            if wdg in self.tier_pairs.keys():
                wdg.itemconfig(1, fill='black')
                self.tier_pairs[wdg].itemconfig('all', fill='black')
                self.frames_canvas.itemconfig('all', fill='black')

    def genFrameList(self, event=None, widg=None, x_loc=None, SI=False):
        '''
        Upon click, reads frames within interval from the tags to the text item of that interval,
        and highlights text of clicked interval
        '''
        self.wipeFill()
        if event:
            widg=event.widget
            x_loc=event.x

        if SI==False:
            item = self.my_find_closest(widg, x_loc)
            self.selectedItem = (widg, item)
            self.setSelectedIntvlFrames(self.selectedItem)

        #automatically updates frame
        if not str(self.app.frame) in self.selectedIntvlFrames:
            if self.selectedIntvlFrames:
                new_frame = int(self.selectedIntvlFrames[0])
            else:
                frame = self.my_find_closest(self.frames_canvas,x_loc)
                framenum = self.frames_canvas.gettags(frame)[0][5:]
                new_frame = int(framenum)
            if self.firstFrame > new_frame:
                new_frame = self.firstFrame
            elif new_frame > self.lastFrame:
                new_frame = self.lastFrame
            self.app.frame = new_frame
            self.app.framesUpdate()
        else:
            self.paintCanvases()
            self.app.Spectrogram.update()

    def collapse(self, event):
        '''
        collapse or uncollapse selected tier
        '''
        widg = event.widget

        if event.num == 1:
            h = self.collapse_height
            if int(widg['height']) == h:
                h = self.canvas_height
        elif event.num == 4 or event.delta > 0:
            h = self.canvas_height
        else:
            h = self.collapse_height

        if int(widg['height']) == h:
            return
        elif h == self.canvas_height:
            mv = (self.canvas_height - self.collapse_height - 14) / 2
        else:
            mv = (self.collapse_height + 14 - self.canvas_height) / 2
        # manually shifting the text by 7 pixels is a rather ugly hack,
        # but it works - DS

        if widg in self.tier_pairs:
                l, c = widg, self.tier_pairs[widg]
        else:
                c = widg
                l = None
                for k in self.tier_pairs:
                        if self.tier_pairs[k] == widg:
                                l = k
                                break
        l.configure(height=h)
        c.configure(height=h)
        l.move('all', 0, mv)
        self.app.event_generate('<Configure>')

    def paintCanvases(self):
        '''

        '''
        if self.selectedItem:
            wdg,itm = self.selectedItem
            #paint selected
            if wdg.type(itm) == 'text':
                wdg.itemconfig(itm, fill='blue')
                #paint boundaries of selected
                if itm+1 in wdg.find_all():
                    wdg.itemconfig(itm+1, fill='blue')
                if itm-1 in wdg.find_all():
                    wdg.itemconfig(itm-1, fill='blue')
            if wdg in self.tier_pairs.keys(): #if on tier-label canvas
                canvas = self.tier_pairs[wdg]
                for el in canvas.find_all():
                    # #make all text intervals blue
                    # if canvas.type(canvas.find_withtag(el)) == 'text':
                    canvas.itemconfig(el, fill='blue')

            #paint frames
            frames = wdg.gettags(itm)
            for frame in frames:
                if frame[:5] == 'frame':
                    frame_obj = self.frames_canvas.find_withtag(frame)
                    #detect whether frame contains any traces
                    framenum = frame[5:]
                    if framenum in self.app.Data.getCurrentTraceTracedFrames():
                        fill = 'blue'
                    else:
                        fill = 'dodger blue'
                    self.frames_canvas.itemconfig(frame_obj, fill=fill)

        #current frame highlighted in red
        if self.app.frame:
            self.highlighted_frame = self.frames_canvas.find_withtag('frame'+str(self.app.frame))
            self.frames_canvas.itemconfig(self.highlighted_frame, fill='red')

    def update(self):
        '''

        '''
        # debug(self.frames_canvas)
        #create list of displayed frames' tags
        itrobj = []
        for itm in self.frames_canvas.find_all():
            itrobj += list(self.frames_canvas.gettags(itm))
        #if selected frame is out of view
        if "frame"+str(self.app.frame) not in itrobj:
            duration = self.end - self.start
            #recenter view on selected frame
            new_time = self.TextGrid.getFirst(self.frameTierName)[self.app.frame-1].time
            self.start = new_time - (duration/2)
            self.end = new_time + (duration/2)
            #redraw
            self.fillCanvases()
        self.wipeFill()
        #if selected frame outside selected interval, select interval on same tier containing frame
        if self.selectedItem:
            if self.selectedItem[0] in self.tier_pairs.keys() or self.selectedItem[0] in self.tier_pairs.values():
                if "frame"+str(self.app.frame) not in self.selectedItem[0].gettags(self.selectedItem[1]): #FIXME should also detect if on label canvas
                    widg = self.selectedItem[0]
                    if widg in self.tier_pairs:
                        widg = self.tier_pairs[widg]
                    new_interval = widg.find_withtag("frame"+str(self.app.frame))[0]
                    self.selectedItem = (self.selectedItem[0], new_interval)

        # repaint all frames
        self.paintCanvases()
        self.updateTimeLabels()

    def grid(self, event=None):
        '''
        Wrapper for gridding all of our Tk widgets.  This funciton assumes that the tiers (as
        specified in the actual TextGrid files) are in some sort of reasonable order, with the
        default label being drawn on top.
        '''
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

    def grid_remove(self):
        raise NotImplementedError('cannot grid_remove the TextGridModule')

    def openSearch(self, event=None):
        self.app.Search.openSearch()
