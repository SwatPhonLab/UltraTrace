#!/usr/bin/env python3

import tkinter
import math
from sys import argv

filebase = argv[1]
radius = 5
click = None
dot = None
line = None
point = None

window = tkinter.Tk(className="measure from point: %s" % filebase)

baselineStart = (299,599-45)
baselineEnd = (68,599-252)

#image = Image.open(argv[1] if len(argv) >=2 else "018_516.png")
image = tkinter.PhotoImage(file=filebase+".png")
canvas = tkinter.Canvas(window, width=image.width(), height=image.height())
canvas.pack()
#image_tk = ImageTk.PhotoImage(image)
canvas.create_image(image.width()/2, image.height()/2, image=image)
canvas.create_line(baselineStart[0], baselineStart[1], baselineEnd[0], baselineEnd[1], fill="blue")

def line_intersection(line1, line2):
    xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1]) #Typo was here

    def det(a, b):
        return a[0] * b[1] - a[1] * b[0]

    div = det(xdiff, ydiff)
    if div == 0:
       raise Exception('lines do not intersect')

    d = (det(*line1), det(*line2))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    return x, y


def callback(event):
	global click
	global dot
	global line
	global point
	lastClick = click	
	click = (event.x, event.y)
	#print("clicked at: ", event.x, event.y)
	lastDot = dot
	dot = canvas.create_oval(event.x-radius, event.y-radius, event.x+radius, event.y+radius, fill='red')
	if lastClick:
		if line:
			canvas.delete(line)
		line = canvas.create_line(lastClick[0], lastClick[1], click[0], click[1], fill='red')
		thislineStart = (lastClick[0], lastClick[1])
		thislineEnd = (click[0], click[1])
		canvas.delete(lastDot)

		if point:
			canvas.delete(point)
		intersectionPoint = line_intersection((baselineStart, baselineEnd), (thislineStart, thislineEnd))
		point = canvas.create_oval(intersectionPoint[0]-radius, intersectionPoint[1]-radius, intersectionPoint[0]+radius, intersectionPoint[1]+radius, fill="purple")
		#print(intersectionPoint)
		hypotenuse = math.hypot(intersectionPoint[0] - baselineStart[0], intersectionPoint[1] - baselineStart[1])
		#print(hypotenuse)
		with open(filebase+".measurement", 'w') as measurementFile:
			measurementFile.write(str(hypotenuse))

canvas.bind("<Button-1>", callback)
#canvas.bind("<31>", lambda event: w.focus_set())
#canvas.bind("<13>", window.destroy)
canvas.bind("<Button-3>", lambda e: window.destroy())
window.mainloop()

#181,547
#75,452


#from tkinter import *          
#
#root = Tk()                    
#
#photo = tkinter.PhotoImage(file="018_516.png")
#photo_label = Label(image=photo)
#photo_label.grid()             
#photo_label.image = photo      
#
#text = Label(text="Text") # included to show background color
#text.grid()    
#
#root.mainloop()
