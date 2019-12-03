from ..util import CROSSHAIR_SELECT_RADIUS
from ..util.logging import *

import math

class Crosshairs:
    def __init__(self, zframe, x, y, color, transform=True):
        '''
        Crosshairs() serves two purposes:
            - handling (visual) placement of a `+` onto the zframe canvas
            - keeping track of point locations for saving/loading trace data

        @param
            zframe :    reference to the ZoomFrame containing the tracing canvas
            x :         x-canvas-coordinate of where we should place the center of the Crosshairs
            y :         y-canvas-coordinate of where we should place the center of the Crosshairs
            color :     color for when unselected
            transform : Boolean RE whether the coordinates need to be adjusted
        '''

        # keep a reference to the zframe
        self.zframe = zframe

        # set defaults here
        self.selectedColor  = 'blue'
        self.unselectedColor= color
        self.selectedWidth  = 1.5#3
        self.unselectedWidth= 1#2

        # store position data
        self.x, self.y = x, y
        self.trueX, self.trueY = x, y
        if transform:
            self.trueX, self.trueY = self.transformCoordsToTrue(x, y)
        else:
            self.x, self.y = self.transformTrueToCoords(x, y)

        self.len = self.transformLength( CROSSHAIR_SELECT_RADIUS )
        # self.resetTrueCoords()
        self.isSelected = False
        self.isVisible = True

        # draw on the canvas
        self.hline = self.zframe.canvas.create_line(self.x-self.len, self.y, self.x+self.len, self.y, fill=self.unselectedColor, width=self.unselectedWidth)
        self.vline = self.zframe.canvas.create_line(self.x, self.y-self.len, self.x, self.y+self.len, fill=self.unselectedColor, width=self.unselectedWidth)

    # def resetTrueCoords(self):
    #   '''
    #   This function calculates the `true` coordinates for saving our crosshairs to the metadata file.
    #   The values are calculated relative to the top left corner of the canvas at 1x zoom.  We need to
    #   make sure to call this every time we change the position of a Crosshairs.
    #   '''
    #   #self.trueX, self.trueY = self.transformCoordsToTrue(self.x,self.y)
    #   pass

    def getTrueCoords(self):
        ''' called when we're saving to file '''
        return self.trueX, self.trueY

    def transformCoordsToTrue(self, x, y):
        '''
        canvas coords -> absolute coords
        absolute coords are % along each axis (e.g. center of image = [.5,.5])
        '''
        # x = (self.trueX - self.zframe.panX) / self.zframe.imgscale
        # y = (self.trueY - self.zframe.panY) / self.zframe.imgscale
        # return x,y
        truex = (x-self.zframe.panX)/(self.zframe.width*self.zframe.imgscale)
        truey = (y-self.zframe.panY)/(self.zframe.height*self.zframe.imgscale)
        # truex = (x-self.zframe.panX)/self.zframe.imgscale
        # truey = (y-self.zframe.panY)/self.zframe.imgscale
        debug(truex, truey)
        return truex, truey

    def transformTrueToCoords(self, truex, truey):
        '''
        absolute coords -> canvas coords
        absolute coords are % along each axis (e.g. center of image = [.5,.5])
        '''
        # x = (_x * self.zframe.imgscale) + self.zframe.panX
        # y = (_y * self.zframe.imgscale) + self.zframe.panY
        x = truex * self.zframe.width * self.zframe.imgscale + self.zframe.panX
        y = truey * self.zframe.height * self.zframe.imgscale + self.zframe.panY
        return x, y

    def transformCoords(self, x, y):
        ''' transforms coordinates by the canvas offsets '''
        x += self.zframe.canvas.canvasx(0)
        y += self.zframe.canvas.canvasy(0)
        return x,y

    def transformLength(self, l):
        ''' transforms a length by our current zoom-amount '''
        return l * self.zframe.imgscale

    def getDistance(self, click):
        ''' calculates the distance from centerpoint to a click event '''
        click = self.transformCoords(*click)
        dx = abs( self.x - click[0] )
        dy = abs( self.y - click[1] )
        return math.sqrt( dx**2 + dy**2 ) if self.isVisible else float('inf') # invisible points infinitely far away

    def select(self):
        ''' select this Crosshairs '''
        if self.isVisible:
            self.zframe.canvas.itemconfig( self.hline, fill=self.selectedColor, width=self.selectedWidth)
            self.zframe.canvas.itemconfig( self.vline, fill=self.selectedColor, width=self.selectedWidth)
            self.isSelected = True

    def unselect(self):
        ''' stop selecting this Crosshairs '''
        if self.isVisible:
            self.zframe.canvas.itemconfig( self.hline, fill=self.unselectedColor, width=self.unselectedWidth)
            self.zframe.canvas.itemconfig( self.vline, fill=self.unselectedColor, width=self.unselectedWidth)
            self.isSelected = False

    def undraw(self):
        ''' use this instead of deleting objects to make undos easier '''
        self.zframe.canvas.itemconfigure( self.hline, state='hidden' )
        self.zframe.canvas.itemconfigure( self.vline, state='hidden' )
        self.unselect()
        self.isVisible = False

    def draw(self):
        ''' called when we undo a delete '''
        self.zframe.canvas.itemconfigure( self.hline, state='normal' )
        self.zframe.canvas.itemconfigure( self.vline, state='normal' )
        self.isVisible = True

    def dragTo(self, click):
        ''' move the centerpoint to a given point (calculated in main class) '''
        if self.isVisible:

            self.x += (click[0] - self.x)
            self.y += (click[1] - self.y)
            # self.x, self.y = self.transformTrueToCoords(self.trueX, self.trueY)
            self.trueX, self.trueY = self.transformCoordsToTrue(self.x, self.y)
            self.len = self.transformLength( CROSSHAIR_SELECT_RADIUS )
            self.zframe.canvas.coords( self.hline, self.x-self.len, self.y, self.x+self.len, self.y )
            self.zframe.canvas.coords( self.vline, self.x, self.y-self.len, self.x, self.y+self.len )

    def recolor(self, color):
        ''' change the fill color of the Crosshairs '''
        if self.isVisible:
            self.unselectedColor = color # change this in the background (i.e. don't unselect)
            if self.isSelected == False:
                self.zframe.canvas.itemconfig( self.hline, fill=color )
                self.zframe.canvas.itemconfig( self.vline, fill=color )
