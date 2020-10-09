from .textgrid import TextGrid
from .base import Module
from ..util.logging import *

import re

from tkinter import Toplevel, StringVar, Grid
from tkinter.ttk import Treeview, Button, Entry, Label, Scrollbar

class Search(Module):
    def __init__(self, app):
        self.app = app
        self.window = None

        self.context_size = 3
        self.results = []
        self.regex = StringVar(self.app)

        # if anything ever changes the contents of any intervals
        # it should call SearchModule.loadIntervals()
        self.intervals = []
        self.loadIntervals()
    def handleClose(self, event=None):
        self.window.destroy()
        self.window = None
    def createWindow(self):
        self.window = Toplevel(self.app)
        self.window.title('Search')
        self.window.protocol("WM_DELETE_WINDOW", self.handleClose)
        self.input = Entry(self.window, textvariable=self.regex)
        self.input.grid(row=0, column=0)
        self.input.bind('<Return>', self.search)
        self.input.bind('<Escape>', lambda ev: self.window.focus())
        self.searchButton = Button(self.window, text='Search', command=self.search, takefocus=0)
        self.searchButton.grid(row=0, column=1)
        self.resultCount = Label(self.window, text='0 results')
        self.resultCount.grid(row=0, column=2)
        cols = ('File', 'Tier', 'Time', 'Text')
        self.scroll = Scrollbar(self.window, orient='vertical')
        self.resultList = Treeview(self.window, columns=cols, show="headings", yscrollcommand=self.scroll.set, selectmode='browse')
        self.scroll.config(command=self.resultList.yview)
        for col in cols:
            self.resultList.heading(col, text=col)
        self.resultList.grid(row=2, column=0, columnspan=3, sticky='news')
        self.resultList.bind('<Double-1>', self.onClick)
        Grid.rowconfigure(self.window, 2, weight=1)
        Grid.columnconfigure(self.window, 0, weight=1)
        self.scroll.grid(row=2, column=3, sticky='ns')
    def openSearch(self):
        if self.window == None:
            self.createWindow()
        self.window.lift()
        self.input.focus()
    def loadIntervals(self):
        filecount = len(self.app.Data.getTopLevel('files'))
        self.intervals = []
        for f in range(filecount):
            filename = self.app.Data.getFileLevel('name', f)
            tg = self.app.Data.checkFileLevel('.TextGrid', f, shoulderror=False)
            if tg:
                grid = self.app.TextGrid.fromFile(tg)
                for tier in grid:
                    if TextGrid.isIntervalTier(tier):
                        for el in tier:
                            if el.mark:
                                self.intervals.append((el, tier.name, filename))
    def search(self, event=None):
        if self.regex.get() == '':
            self.results = []
        else:
            pat = re.compile(self.regex.get(), re.IGNORECASE | re.MULTILINE | re.DOTALL)
            self.results = []
            for i in self.intervals:
                s = pat.search(i[0].mark)
                if s:
                    disp = i[0].mark
                    a = max(0, s.start()-self.context_size)
                    b = min(s.end()+self.context_size, len(disp))
                    self.results.append(i + (('...' if a > 0 else '')+disp[a:b]+('...' if b < len(disp) else ''),))
        self.resultCount.configure(text='%s results' % len(self.results))
        for kid in self.resultList.get_children():
            self.resultList.delete(kid)
        for row, res in enumerate(self.results):
            ls = (res[2], res[1], '%s-%s' % (res[0].minTime, res[0].maxTime), res[3])
            self.resultList.insert('', 'end', iid=str(row), values=ls)
    def onClick(self, event=None):
        self.jumpTo(int(self.resultList.selection()[0]))
    def jumpTo(self, index):
        self.app.filesJumpTo(self.results[index][2])
        self.app.TextGrid.selectedTier.set(self.results[index][1])
        self.app.TextGrid.start = self.results[index][0].minTime
        self.app.TextGrid.end = self.results[index][0].maxTime
        for i, f in enumerate(self.app.TextGrid.frameTier):
            if f.time >= self.results[index][0].minTime:
                self.app.frameSV.set(str(i))
                self.app.framesJumpTo()
                break
        self.app.TextGrid.fillCanvases()

    def reset(self, *args, **kwargs):
        raise NotImplementedError('cannot call SearchModule::reset')

    def update(self, *args, **kwargs):
        raise NotImplementedError('cannot call SearchModule::update')

    def grid(self, *args, **kwargs):
        raise NotImplementedError('cannot call SearchModule::grid')

    def grid_remove(self, *args, **kwargs):
        raise NotImplementedError('cannot call SearchModule::grid_remove')
