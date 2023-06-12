from .base import Module
from .. import util
from ..util.logging import *
from ..widgets import Header

import queue
import threading
import time
import math

from tkinter.ttk import Button, Frame

AUDIO_LIBS_INSTALLED = False
try:
    from pydub import AudioSegment
    import pyaudio
    AUDIO_LIBS_INSTALLED = True
except ImportError as e:
    warn(e)

VIDEO_LIBS_INSTALLED = False
try:
    from PIL import Image, ImageTk, ImageDraw, ImageEnhance
    VIDEO_LIBS_INSTALLED = True
except ImportError as e:
    warn(e)

class Playback(Module):
    '''
    Module to handle playback of audio and video files.
    '''
    def __init__(self, app):
        self.app = app
        self.current = None
        if AUDIO_LIBS_INSTALLED:
            info( ' - initializing module: Audio' )
            self.sfile = None
            self.p = pyaudio.PyAudio()
            self.currentInterval = None
            self.started = False
            self.paused = False
            self.sync = threading.Event()
            self.stoprequest = threading.Event()

            # widget management
            #self.frame = Frame(self.app.BOTTOM)
            self.frame = Frame(self.app.LEFT)#, pady=7)

            self.header = Header(self.frame, text="Playback")
            self.playBtn = Button(self.frame, text="⏯", command=self.playpauseAV, state='disabled', takefocus=0) # NOTE: not currently appearing
            self.app.bind('<space>', self.playpauseAV )
            self.app.bind('<Escape>', self.stopAV )
        if VIDEO_LIBS_INSTALLED:
            info( ' - initializing module: Video' )
            self.app.bind('<space>', self.playpauseAV )
            self.app.bind('<Escape>', self.stopAV )
        self.grid()
        self.reset()

    def update(self):
        '''
        don't change the audio file when we change frames
        '''
        pass

    def reset(self):
        '''
        try to load an audio file
        '''
        if AUDIO_LIBS_INSTALLED:
            self.current = None
            audioFallbacks = [ '.wav', '.flac', '.ogg', '.mp3' ]
            for codec in audioFallbacks:
                if self.loadAudio( codec ) == True:
                    self.playBtn.config( state='normal' )
                    return

    def loadAudio(self, codec):
        '''
        load an audio file with a specific codec
        '''
        audiofile = self.app.Data.getFileLevel( codec )
        if audiofile != None:
            try:
                audiofile = self.app.Data.unrelativize(audiofile)
                self.sfile = AudioSegment.from_file( audiofile )
                self.current = audiofile
                self.duration = len(self.sfile)/1000.0
                return True
            except Exception as e:
                error('Unable to load audio file: `%s`' % audiofile, e)
                return False

    def playpauseAV(self, event=None):
        '''

        '''
        # debug(self.started, self.paused, '1858')
        if self.started == False or self.currentInterval != self.app.TextGrid.selectedItem: #if we haven't started playing or we're in a new interval
            #reset monitoring variables
            self.currentInterval = self.app.TextGrid.selectedItem
            self.started = False
            self.paused = False

            if self.app.TextGrid.selectedItem:
                start, end = self.app.TextGrid.getMinMaxTime()
            else:
                start = self.app.TextGrid.start
                end = self.app.TextGrid.end

            # if VIDEO_LIBS_INSTALLED and AUDIO_LIBS_INSTALLED:
            #   self.readyVideo()
            #   self.readyAudio(start, end)
            #   self.playAudio()
            # elif AUDIO_LIBS_INSTALLED:
            #   self.readyAudio(start, end)
            #   self.playAudio()
            # elif VIDEO_LIBS_INSTALLED:
            #   self.readyVideo()
            #   self.dicomframeQ = queue.Queue()
            #   for i in range(len(self.pngs)):
            #       self.dicomframeQ.put(self.pngs[i])
            #   self.playVideoNoAudio()

            if self.app.Dicom.isLoaded():
                self.readyVideo()
            if AUDIO_LIBS_INSTALLED:
                self.readyAudio(start, end)
                self.playAudio()
            elif self.app.Dicom.isLoaded():
                self.dicomframeQ = queue.Queue()
                for i in range(len(self.pngs)):
                    self.dicomframeQ.put(self.pngs[i])
                self.playVideoNoAudio()

        elif self.started == True:
            if self.paused == False:
                self.paused = True
                self.stream.stop_stream()
            else:
                self.paused = False
                self.playAudio()

    def readyAudio(self, start, end):
        '''

        '''
        #audio stuff
        start_idx = round(float(start)*1000)
        end_idx = round(float(end)*1000)
        self.flen = float(self.app.TextGrid.frame_len)
        fpb = 512
        extrafs = (end_idx-start_idx)%fpb
        extrasecs = extrafs/self.sfile.frame_rate
        pad = AudioSegment.silent(duration=round(extrasecs*1000))
        seg_nopad = self.sfile[start_idx:end_idx]
        self.seg = seg_nopad + pad
        # seg.append()
        self.audioframe = 0

        # open stream using callback (3)
        self.stream = self.p.open(format=self.p.get_format_from_width(self.seg.sample_width),
                        channels=self.seg.channels,
                        rate=self.seg.frame_rate,
                        frames_per_buffer=fpb,
                        output=True,
                        start=False,
                        stream_callback=self.callback)

        # debug(self.seg.frame_count()/fpb, 'number of chunks')
        # debug(self.seg.frame_count()%fpb, 'last chunk size')
        # self.chunkcount = 0

    def readyVideo(self):
        '''

        '''
        self.app.Trace.reset()
        tags = self.app.TextGrid.selectedItem[0].gettags(self.app.TextGrid.selectedItem[1])
        framenums = [tag[5:] for tag in tags if tag[:5]=='frame']
        self.framestart = int(framenums[0])
        imgs = self.app.Dicom.getFrames(framenums)
        canvas = self.app.Dicom.zframe.canvas
        bbox = canvas.bbox(canvas.find_all()[0])
        dim = (bbox[2] - bbox[0], bbox[3] - bbox[1])
        self.pngs = []
        traces = self.app.Data.getTopLevel('traces')
        file = self.app.Data.getCurrentFilename()
        l = util.CROSSHAIR_SELECT_RADIUS
        for frame, img in zip(framenums, imgs):
            img = img.resize(dim)
            draw = ImageDraw.Draw(img)
            for name in traces:
                color = traces[name]['color']
                if file in traces[name]['files'] and frame in traces[name]['files'][file]:
                    for pt in traces[name]['files'][file][frame]:
                        x = int(pt['x'] * img.width)
                        y = int(pt['y'] * img.height)
                        draw.line((x-l, y, x+l, y), fill=color)
                        draw.line((x, y-l, x, y+l), fill=color)
            del draw
            self.pngs.append(ImageTk.PhotoImage(img))

        #video w/audio stuff
        self.dicomframe_timer = 0
        self.dicomframe_num = 1
        self.dicomframeQ = queue.Queue()
        self.dicomframeQ.put(self.pngs[0]) #put now, because audio callback puts frames when audio segments end
        # for i in range(len(self.pngs)):
        #   self.dicomframeQ.put(self.pngs[i])

    def callback(self, in_data, frame_count, time_info, status):
        '''
        Called by pyaudio stream. Gets chunks of audio ready for playing
        With video capabilities, also updates video frame information
        '''
        # self.sync.clear()
        # self.chunkcount+=1
        data = b''.join([self.seg.get_frame(i) for i in range(self.audioframe, self.audioframe+frame_count)])
        # debug(len(data), 'line 1960')
        self.audioframe+=frame_count

        if self.app.Dicom.isLoaded():
            #check & update video frame
            canvas = self.app.Dicom.zframe.canvas
            callbacklen = frame_count/self.seg.frame_rate
            self.dicomframe_timer += callbacklen
            #go to next frame
            if self.dicomframe_timer % self.flen != self.dicomframe_timer and self.dicomframe_num < len(self.pngs):
                floor = math.floor(self.dicomframe_timer/self.flen)
                # debug(floor, 'line 1961')
                self.dicomframe_timer = self.dicomframe_timer-self.flen*floor
                if floor > 1:
                    for i in range(floor-1):
                        # debug(self.dicomframe_num+self.framestart+i, 'putting frame into Q')
                        if self.dicomframe_num+i < len(self.pngs):
                            self.dicomframeQ.put(self.pngs[self.dicomframe_num+i])
                else:
                    self.dicomframeQ.put(self.pngs[self.dicomframe_num])
                # self.sync.set()
                self.dicomframe_num+=floor

                # debug(self.dicomframe_num, len(self.pngs), 'line 1968')
            # else: #stop video loop
                if self.dicomframe_num >= len(self.pngs):
                    self.stoprequest.set()

        return (data, pyaudio.paContinue)

    def playAudio(self):
        self.stream.start_stream()
        self.started = True
        if self.app.Dicom.isLoaded():
            self.playVideoWithAudio()
        else:
            pass #write a loop that keeps audio playing
        # stop stream (6)
        if self.stoprequest.is_set():
            self.stopAV()
        # self.stream.stop_stream()
        # if self.stoprequest.is_set():
        #   self.stream.close()
        #   self.started = False
        # debug(self.chunkcount)
        # close PyAudio (7)
        # self.p.terminate() # NOTE: needs to be removed in order to play multiple audio files in a row

    def playVideoWithAudio(self):
        '''

        '''
        # self.sync.wait()
        if self.paused == True:
            return
        canvas = self.app.Dicom.zframe.canvas
        # debug(self.dicomframeQ.qsize(),'line 1991')
        try:
            pic = self.dicomframeQ.get(timeout=.5)
            canvas.itemconfig(canvas.find_all()[0] , image=pic )
            # canvas.lift(pic)
            # canvas.img = pic
            canvas.update()
        except Exception as e:
            error(e)
        # debug(pic, 'displayed')
        # debug(self.dicomframe_num+self.framestart, 'displayed')
        if not self.stoprequest.is_set() or not self.dicomframeQ.empty(): #should this if be at the top?
            self.playVideoWithAudio()
            # canvas.after(10, self.playVideoWithAudio)

    def playVideoNoAudio(self):
        '''

        '''
        canvas = self.app.Dicom.zframe.canvas
        # pic = self.dicomframeQ.get()
        pic = self.dicomframeQ.get(block=False)
        canvas.itemconfig( canvas.find_all()[0], image=pic )
        canvas.update()
        if not self.dicomframeQ.empty() and self.stoprequest.is_set() == False: #should this if be at the top?
            self.playVideoNoAudio()

    def stopAV(self,event=None):
        self.stoprequest.set()
        if AUDIO_LIBS_INSTALLED:
            self.stream.stop_stream()
            self.stream.close()
        self.started = False
        self.paused = False
        self.app.framesJumpTo()
        self.stoprequest.clear()

    def grid(self):
        ''' grid widgets '''
        self.frame.grid( row=8 )
        self.header.grid()
        self.playBtn.grid()

    def grid_remove(self):
        ''' remove widgets from grid '''
        self.frame.grid_remove()
        self.header.grid_remove()
        self.playBtn.grid_remove()

