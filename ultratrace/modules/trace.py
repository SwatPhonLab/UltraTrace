from .base import Module
from ..widgets import Crosshairs, Header
import tkinter as tk

class Trace(Module):
    def __init__(self, app):
        data_copy = '''R0lGODlhGAAYAPAAAAAAAAAAACH5BAEAAAEALAAAAAAYABgAAAJHjI+pCe3/1oHUSdOunmDvHFTWBYrjUnbMuWIqAqEqCMdt+HI25yrVTZMEcT3NMPXJEZckJdKorCWbU2H0JqvKTBErl+XZFAAAOw'''
        data_paste = '''R0lGODlhGAAYAPAAAAAAAAAAACH5BAEAAAEALAAAAAAYABgAAAJBjI+pq+DAonlPToqza7rv9FlBeJCSOUJpd3EXm7piDKoi+nkqvnttPaMhUAzeiwJMapJDm8U44+kynCkmiM1qZwUAOw'''
        self.img_copy = tk.PhotoImage(data=data_copy)
        self.img_paste = tk.PhotoImage(data=data_paste)
        self.traceSV = tk.StringVar()
        self.traceSV.set( '' )
        self.frame = tk.Frame(self.app.LEFT)#, pady=7, padx=7)
        self.frame.grid( row=4 )
        lbframe = tk.Frame(self.frame)
        self.scrollbar = tk.Scrollbar(lbframe)
        self.listbox = tk.Listbox(lbframe, yscrollcommand=self.scrollbar.set, width=12, exportselection=False, takefocus=0)
        self.scrollbar.config(command=self.listbox.yview)
        for trace in self.available:
            self.listbox.insert('end', trace)
        for i, item in enumerate(self.listbox.get(0, 'end')):
            self.listbox.selection_clear(0, 'end')
            self.listbox.select_set( i )

        self.TkWidgets = [
            self.getWidget( Header(self.frame, text="Choose a trace"), row=5, column=0, columnspan=4 ),
            self.getWidget( lbframe, row=10, column=0, rowspan=50 ),
            self.getWidget( tk.Button(self.frame, text='Set as default', command=self.setDefaultTraceName, takefocus=0), row=10, column=2, columnspan=2 ),
            self.getWidget( tk.Button(self.frame, text='Select all', command=self.selectAll, takefocus=0), row=11, column=2, columnspan=2 ),
            self.getWidget( tk.Button(self.frame, image=self.img_copy, command=self.copy, takefocus=0), row=12, column=2 ), # FIXME: add tooltip for "Copy"
            self.getWidget( tk.Button(self.frame, image=self.img_paste, command=self.paste, takefocus=0), row=12, column=3 ), # FIXME: add tooltip for "Paste"
            self.getWidget( tk.Entry( self.frame, width=8, textvariable=self.displayedColour), row=13, column=1, columnspan=2, sticky='w'),
            self.getWidget( tk.Button(self.frame, text='Recolor', command=self.recolor, takefocus=0), row=13, column=3 ),
            self.getWidget( tk.Button(self.frame, text='Clear', command=self.clear, takefocus=0), row=15, column=2, columnspan=2 ),
            self.getWidget( tk.Entry( self.frame, width=12, textvariable=self.traceSV), row=100, column=0, sticky='w' ),
            self.getWidget( tk.Button(self.frame, text='New', command=self.newTrace, takefocus=0), row=100, column=2 ),
            self.getWidget( tk.Button(self.frame, text='Rename', command=self.renameTrace, takefocus=0), row=100, column=3 ) ]

        self.TkWidgets[6]['widget'].bind('<Return>', lambda ev: self.TkWidgets[0]['widget'].focus())
        self.TkWidgets[6]['widget'].bind('<Escape>', lambda ev: self.TkWidgets[0]['widget'].focus())
        self.TkWidgets[9]['widget'].bind('<Return>', lambda ev: self.TkWidgets[0]['widget'].focus())
        self.TkWidgets[9]['widget'].bind('<Escape>', lambda ev: self.TkWidgets[0]['widget'].focus())

        if util.get_platform() == 'Linux':
            self.app.bind('<Control-r>', self.recolor )
            self.app.bind('<Control-c>', self.copy )
            self.app.bind('<Control-v>', self.paste )
        else:
            self.app.bind('<Command-r>', self.recolor )
            self.app.bind('<Command-c>', self.copy )
            self.app.bind('<Command-v>', self.paste )
        self.grid()


    def getCurrentTraceName(self):
        return self.listbox.get(self.listbox.curselection())

    def getNearClickAllTraces(self, click):
        self.listbox.selection_clear(0, 'end')
        self.listbox.select_set( i )

    def newTrace(self):
        name = self.traceSV.get()[:12]
        self.traceSV.set('')
        self.listbox.insert('end', name)
        self.listbox.selection_clear(0, 'end')
        self.listbox.select_set( len(self.available)-1 )

    def renameTrace(self, oldName=None, newName=None):
        newName = self.traceSV.get()[:12] if newName==None else newName
        self.traceSV.set('')
        index = self.listbox.curselection()
        self.listbox.delete(index)
        self.listbox.insert(index, newName)
        self.listbox.selection_clear(0, 'end')
        self.listbox.select_set(index)

    def grid(self):
        for item in self.TkWidgets:
            item['widget'].grid(
                row=item['row'], column=item['column'], rowspan=item['rowspan'],
                columnspan=item['columnspan'], sticky=item['sticky'] )
        self.listbox.pack(side='left', fill='y')
        self.scrollbar.pack(side='right', fill='y')

    def grid_remove(self):
        for item in self.TkWidgets:
            item['widget'].grid_remove()
        self.listbox.packforget()
        self.scrollbar.packforget()

