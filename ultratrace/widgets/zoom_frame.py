from tkinter import Canvas
from tkinter.ttk import Frame
from PIL import ImageTk # pillow

from .rect_tracker import RectTracker

class ZoomFrame(Frame):
    '''
    Wrapper for a Tk Frame() object that includes zooming and panning functionality.
    This code is inspired by the answer from https://stackoverflow.com/users/7550928/foo-bar
    at https://stackoverflow.com/questions/41656176/tkinter-canvas-zoom-move-pan ...
    Could probably be cleaned up and slimmed down
    '''
    def __init__(self, master, delta, app):
        Frame.__init__(self, master)
        self.app = app
        self.delta = delta
        self.maxZoom = 5
        #self.resetCanvas(master)

        self.canvas_width = 800
        self.width = 0
        self.canvas_height = 600
        self.height = 0
        self.shown = False
        self.aspect_ratio = 4.0/3.0

        self.canvas = Canvas( master,  bg='grey', width=self.canvas_width, height=self.canvas_height, highlightthickness=0 )
        self.canvas.grid(row=0, column=0, sticky='news')
        self.canvas.update() # do i need
        rect = RectTracker(self.canvas)
        rect.autodraw(outline='blue')

        # self.master.rowconfigure(0, weight=1) # do i need
        # self.master.columnconfigure(0, weight=1) # do i need

        # self.canvas.bind('<Configure>', self.showImage ) # on canvas resize events
        self.canvas.bind('<Control-Button-1>', self.moveFrom )
        self.canvas.bind('<Control-B1-Motion>', self.moveTo )
        self.canvas.bind('<MouseWheel>', self.wheel ) # Windows & Linux
        self.canvas.bind('<Button-4>', self.wheel )   # Linux scroll up
        self.canvas.bind('<Button-5>', self.wheel )   # Linux scroll down

        self.resetCanvas()

        self.canvas.bind('<Button-1>', self.app.onClickZoom )
        self.canvas.bind('<Motion>', self.app.onMotion )

        self.app.bind('<Command-equal>', self.wheel )
        self.app.bind('<Command-minus>', self.wheel )

    def resetCanvas(self):
        self.canvas_width = 800
        self.canvas_height = 600

        # self.canvas = Canvas( master,  bg='grey', width=self.canvas_width, height=self.canvas_height, highlightthickness=0 )
        # self.canvas.grid(row=0, column=0, sticky='news')
        # self.canvas.update() # do i need

        # self.master.rowconfigure(0, weight=1) # do i need
        # self.master.columnconfigure(0, weight=1) # do i need
        #
        # self.canvas.bind('<Configure>', self.showImage ) # on canvas resize events
        # self.canvas.bind('<Control-Button-1>', self.moveFrom )
        # self.canvas.bind('<Control-B1-Motion>', self.moveTo )
        # self.canvas.bind('<MouseWheel>', self.wheel ) # Windows & Linux FIXME
        # self.canvas.bind('<Button-4>', self.wheel )   # Linux scroll up
        # self.canvas.bind('<Button-5>', self.wheel )   # Linux scroll down

        self.origX = self.canvas.xview()[0] - 1
        self.origY = self.canvas.yview()[0] - 150

        self.zoom = 0
        self.imgscale = 1.0
        self.image = None
        self.panStartX = 0
        self.panStartY = 0
        self.panX = 0
        self.panY = 0

    def resetImageDimensions(self):
        self.width = 0
        self.height = 0
        self.aspect_ratio = 1

    def setImage(self, image): # expect an Image() instance
        self.image = image
        if self.width == 0 and image:
            self.width, self.height = self.image.size
            self.aspect_ratio = self.width/self.height
        win_width = self.app.RIGHT.winfo_width()
        asp_height = round(win_width / self.aspect_ratio)
        win_height = self.app.RIGHT.winfo_height()
        asp_width = round(win_height * self.aspect_ratio)
        if asp_height > win_height:
            self.height = win_height
            self.width = asp_width
        else:
            self.height = asp_height
            self.width = win_width
        self.showImage()

    def showImage(self, event=None):
        # even if we're not showing a new frame, we want to remove the old one
        self.canvas.delete('delendum')
        if self.image != None:
            self.container = self.canvas.create_rectangle(0,0,self.width,self.height,width=0, tags='delendum')
            self.canvas.scale('all', 0, 0, self.imgscale, self.imgscale)
            self.canvas.move('all', self.panX, self.panY)
            bbox = self.canvas.bbox(self.container)
            image = self.image.resize((bbox[2] - bbox[0], bbox[3] - bbox[1]))
            imagetk = ImageTk.PhotoImage(image)
            image = self.canvas.create_image(bbox[0], bbox[1], anchor='nw', image=imagetk, tags='delendum')
            self.canvas.lower(image)
            self.canvas.imagetk = imagetk
            self.shown = True
            self.app.Trace.update()

    def wheel(self, event):
        if self.image != None:
            if event.keysym == 'equal' or event.keysym == 'minus': #what is this for?
                x = self.canvas_width/2
                y = self.canvas_height/2
            else:                                                   #do these vars get used?
                x = self.canvas.canvasx(event.x)
                y = self.canvas.canvasy(event.y)

            # Respond to Linux (event.num) or Windows (event.delta) wheel event
            if event.num == 5 or event.delta < 0 or event.keysym == 'minus':  # zoom out
                self.zoomOut()

            elif event.num == 4 or event.delta > 0 or event.keysym == 'equal':  # zoom in
                self.zoomIn()

    def zoomOut(self):
        if self.zoom < self.maxZoom:
            self.zoom += 1
            self.imgscale /= self.delta

        bbox = self.canvas.coords(self.container)
        self.panX = bbox[0]
        self.panY = bbox[1]
        self.showImage()

    def zoomIn(self):
        if self.zoom > self.maxZoom * -1:
            self.zoom -= 1
            self.imgscale *= self.delta

        bbox = self.canvas.coords(self.container)
        self.panX = bbox[0]
        self.panY = bbox[1]
        self.showImage()

    def scrollY(self, *args, **kwargs):
        self.canvas.yview(*args, **kwargs)
        self.showImage()

    def moveFrom(self, event):
        self.panStartX = event.x
        self.panStartY = event.y

    def moveTo(self, event):
        dx = event.x - self.panStartX
        dy = event.y - self.panStartY
        self.panStartX = event.x
        self.panStartY = event.y
        self.panX += dx
        self.panY += dy
        self.showImage()
