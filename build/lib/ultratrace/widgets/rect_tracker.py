class RectTracker:
    ''' Copied from http://code.activestate.com/recipes/577409-python-tkinter-canvas-rectangle-selection-box/'''

    def __init__(self, canvas):
        self.canvas = canvas
        self.item = None

    def draw(self, start, end, **opts):
        """Draw the rectangle"""
        return self.canvas.create_rectangle(*(list(start)+list(end)), **opts)

    def autodraw(self, **opts):
        """Setup automatic drawing; supports command option"""
        self.start = None
        # self.canvas.bind("<Shift-Button-1>", self.__update, '+')
        self.canvas.bind("<Shift-B1-Motion>", self.__update, '+')
        self.canvas.bind("<ButtonRelease-1>", self.__stop, '+')

        self._command = opts.pop('command', lambda *args: None)
        self.rectopts = opts

    def __update(self, event):
        if not self.start:
            self.start = [event.x, event.y]
            # return

        if self.item is not None:
            self.canvas.delete(self.item)
        self.item = self.draw(self.start, (event.x, event.y), **self.rectopts)
        self._command(self.start, (event.x, event.y))

    def __stop(self, event):
        self.start = None
        self.canvas.delete(self.item)
        self.item = None
