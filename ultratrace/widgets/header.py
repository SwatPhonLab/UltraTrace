from tkinter.ttk import Label

class Header(Label):
    def __init__(self, master, text):
        '''
        Wrapper for Tk Label() object with a specified font
        '''
        Label.__init__(self, master, text=text, font='TkDefaultFont 12 bold')
