#!/usr/bin/env python3

import tkinter
import math
from sys import argv
import json

filebase = argv[1]
radius = 5
click = None

window = tkinter.Tk(className="measure from point: %s" % filebase)

baselineStart = (299,599-45)
baselineEnd = (68,599-252)
reference = (baselineStart, baselineEnd)
### format = {"TR": {'reference': ((x, y), (x, y)), 'userline': ((x, y), (x, y)), 'intersection': (x, y), 'measurement': x}}

measurementFn = filebase+".measurement"
#colours = {"TR": {"points": "MediumPurple1"}, "TB": {"dots": "lightgreen"}}
colours = {"TR": {"points": "MediumPurple1"}, "TB": {"points": "SeaGreen1", "lines": "SeaGreen2", "references": "SteelBlue1"}}


#image = Image.open(argv[1] if len(argv) >=2 else "018_516.png")
image = tkinter.PhotoImage(file=filebase+".png")
canvas = tkinter.Canvas(window, width=image.width(), height=image.height())
canvas.pack()
#image_tk = ImageTk.PhotoImage(image)
canvas.create_image(image.width()/2, image.height()/2, image=image)
canvas.create_line(baselineStart[0], baselineStart[1], baselineEnd[0], baselineEnd[1], fill="blue")

def line_intersection(line1, line2):
	xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
	ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

	def det(a, b):
		return a[0] * b[1] - a[1] * b[0]

	div = det(xdiff, ydiff)
	if div == 0:
	   raise Exception('lines do not intersect')

	d = (det(*line1), det(*line2))
	x = det(d, xdiff) / div
	y = det(d, ydiff) / div
	return x, y

def measurement2coordinates(source, end, distance):
	(sourceX, sourceY) = source
	(endX, endY) = end

	# calculate vector from source to end
	vectorX = float(endX - sourceX)
	vectorY = float(endY - sourceY)

	# calculate proportion of hypotenuse
	factor = distance / math.sqrt(vectorX * vectorX + vectorY * vectorY)

	# factor the lengths
	vectorX *= factor
	vectorY *= factor

	# calculate the new vector
	point = (int(sourceX + vectorX), int(sourceY + vectorY))

	return point

def writeData(fDict):
	global measurementFn
	with open(measurementFn, 'w') as measurementFile:
		measurementFile.write(json.dumps(fDict, sort_keys=True, indent=3))
	print(fDict)

def loadFile(fn):
	fDict = {}
	with open(fn, 'r') as dataFile:
		fileContents = dataFile.read()
	fType = type(json.loads(fileContents))
	# if it's an old-format file:
	if fType == float:
		print("old format file detected")
		measurement = json.loads(fileContents)
		intersection = measurement2coordinates(reference[0], reference[1], measurement)
		fDict = {'TR': {'reference': reference, 'measurement': measurement, 'intersection': intersection, 'type': 'vector'}, 'TB': {'type': 'point', 'reference': (425, 591)}}
		writeData(fDict)
	# if it's a new-format file:
	elif fType == dict:
		fDict = json.loads(fileContents)

	return fDict

def callback(event):
	global click
	global dots
	global lines
	global points
	global fDict
	global reference
	global listbox
	global colours
	curMeasure = listbox.get(listbox.curselection())
	curMeasureType = fDict[curMeasure]['type']

	lastClick = click	
	click = (event.x, event.y)
	#print("clicked at: ", event.x, event.y)
	if curMeasureType == "vector":
		lastDot = dots[curMeasure]
		dots[curMeasure] = canvas.create_oval(event.x-radius, event.y-radius, event.x+radius, event.y+radius, fill='red')
		if lastClick:
			if curMeasure in lines:
				canvas.delete(lines[curMeasure])
			lines[curMeasure] = canvas.create_line(lastClick[0], lastClick[1], click[0], click[1], fill='red')
			thislineStart = (lastClick[0], lastClick[1])
			thislineEnd = (click[0], click[1])
			thisLine = (thislineStart, thislineEnd)
			canvas.delete(lastDot)
	
			if curMeasure in points:
				canvas.delete(points[curMeasure])
			intersectionPoint = line_intersection(references[curMeasure], thisLine)
			points[curMeasure] = canvas.create_oval(intersectionPoint[0]-radius, intersectionPoint[1]-radius, intersectionPoint[0]+radius, intersectionPoint[1]+radius, outline=colours[curMeasureType]["points"])
			#print(intersectionPoint)
			hypotenuse = math.hypot(intersectionPoint[0] - baselineStart[0], intersectionPoint[1] - baselineStart[1])
			#print(hypotenuse)
			fDict[curMeasure]['measurement'] = hypotenuse
			fDict[curMeasure]['intersection'] = intersectionPoint
			fDict[curMeasure]['userline'] = (thislineStart, thislineEnd)
			writeData(fDict)
	elif curMeasureType == "point":
		lastPoint = points[curMeasure]
		points[curMeasure] = canvas.create_oval(event.x-radius, event.y-radius, event.x+radius, event.y+radius, outline=colours[curMeasure]["points"])
		#if lastClick:
		if curMeasure in lines:
			for line in lines[curMeasure]:
				canvas.delete(line)
		canvas.delete(lastPoint)
		lines[curMeasure] = (
			canvas.create_line(click[0]-50, click[1], click[0]+50, click[1], fill=colours[curMeasure]["lines"]),
			canvas.create_line(click[0], click[1]-50, click[0], click[1]+50, fill=colours[curMeasure]["lines"])
		)
		intersectionPoint = (click[0], click[1])
		Dx = fDict[curMeasure]['reference'][0] - intersectionPoint[0]
		Dy = fDict[curMeasure]['reference'][1] - intersectionPoint[1]
		fDict[curMeasure]['intersection'] = intersectionPoint
		fDict[curMeasure]['measurement'] = (Dx, Dy)
		writeData(fDict)
			

#global fDict
fDict = loadFile(measurementFn)
lines = {}
dots = {}
points = {}
references = {}

for measure in fDict:
	if fDict[measure]['type'] == "vector":
		if "userline" in fDict[measure]:
			((x1, y1), (x2, y2)) = fDict[measure]['userline']
			lines[measure] = canvas.create_line(x1, y1, x2, y2, fill='red')
		else:
			lines[measure] = None
		if "intersection" in fDict[measure]:
			(thisX, thisY) = fDict[measure]['intersection']
			points[measure] = canvas.create_oval(thisX-radius, thisY-radius, thisX+radius, thisY+radius, outline=colours[measure]["points"])
		else:
			points[measure] = None
		if "reference" in fDict[measure]:
			references[measure] = fDict[measure]['reference']
	elif fDict[measure]['type'] == "point":
		if "intersection" in fDict[measure]:
			(thisX, thisY) = fDict[measure]['intersection']
			points[measure] = canvas.create_oval(thisX-radius, thisY-radius, thisX+radius, thisY+radius, outline=colours[measure]["points"])
			lines[measure] = (
				canvas.create_line(thisX-50, thisY, thisX+50, thisY, fill=colours[measure]["lines"]),
				canvas.create_line(thisX, thisY-50, thisX, thisY+50, fill=colours[measure]["lines"])
			)

		if "reference" in fDict[measure]:
			(thisX, thisY) = fDict[measure]['reference']
			references[measure] = canvas.create_oval(thisX-radius, thisY-radius, thisX+radius, thisY+radius, outline=colours[measure]["references"])

	dots[measure] = None
	

canvas.bind("<Button-1>", callback)
#canvas.bind("<31>", lambda event: w.focus_set())
#canvas.bind("<13>", window.destroy)
canvas.bind("<Button-3>", lambda e: window.destroy())


listbox = tkinter.Listbox(window, height=3)
listbox.pack()

#listbox.insert(tkinter.END, "a list entry")

for item in sorted(fDict):
	listbox.insert(tkinter.END, item)
listbox.selection_set(0)

subWindow = canvas.create_window((150,90), window=listbox, anchor="nw")

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
