from .base import Module
import tkinter as tk

class Search(Module):
    def __init__(self, app):
        self.regex = tk.StringVar(self.app)
    def handleClose(self, event=None):
        self.window.destroy()
        self.window = None
    def createWindow(self):
        self.window = tk.Toplevel(self.app)
        self.window.title('Search')
        self.window.protocol("WM_DELETE_WINDOW", self.handleClose)
        self.input = tk.Entry(self.window, textvariable=self.regex)
        self.input.grid(row=0, column=0)
        self.input.bind('<Return>', self.search)
        self.input.bind('<Escape>', lambda ev: self.window.focus())
        self.searchButton = tk.Button(self.window, text='Search', command=self.search, takefocus=0)
        self.searchButton.grid(row=0, column=1)
        self.resultCount = tk.Label(self.window, text='0 results')
        self.resultCount.grid(row=0, column=2)
        cols = ('File', 'Tier', 'Time', 'Text')
        self.scroll = tk.Scrollbar(self.window, orient='vertical')
        self.resultList = tk.Treeview(self.window, columns=cols, show="headings", yscrollcommand=self.scroll.set, selectmode='browse')
        self.scroll.config(command=self.resultList.yview)
        for col in cols:
            self.resultList.heading(col, text=col)
        self.resultList.grid(row=2, column=0, columnspan=3, sticky='news')
        self.resultList.bind('<Double-1>', self.onClick)
        Grid.rowconfigure(self.window, 2, weight=1) # ?
        Grid.columnconfigure(self.window, 0, weight=1) # ?
        self.scroll.grid(row=2, column=3, sticky='ns')
    def openSearch(self):
        self.window.lift()
        self.input.focus()
    def search(self, event=None):
        self.resultCount.configure(text='%s results' % len(self.results))
        for kid in self.resultList.get_children():
            self.resultList.delete(kid)
        for row, res in enumerate(self.results):
            self.resultList.insert('', 'end', iid=str(row), values=ls)
    def onClick(self, event=None):
        pass
    def jumpTo(self, index):
        self.app.frameSV.set(str(i))
