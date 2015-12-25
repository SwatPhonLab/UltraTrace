#!/usr/bin/env python3

import tkinter
import math
from sys import argv
import json
import os



#def traceClicks():
#	print("tracing?")
#
#	window.after(500, traceClicks)
#			
#	



class markingGUI(tkinter.Tk):
	def __init__(self):
		tk.Tk.__init__(self)

		self.setDefaults()

		self.className="mark points: %s" % self.filebase

		self.canvas.bind("<Button-1>", self.onLeftClick)
		self.canvas.bind("<Button-3>", lambda e: self.destroy())
		self.listbox = tkinter.Listbox(self, height=3)
		self.listbox.pack()

		# load and process file
		self.loadFile(self.measurementFn)
		self.afterLoad()

		self.populateList()
		self.subWindow = self.canvas.create_window((150,90),
			window=self.listbox, anchor="nw")

	
	def setDefaults:
		self.filebase = argv[1]
		radius = 5
		click = None

		baselineStarts = {}
		baselineStarts["2014-10-09"] = (299,599-45)
		baselineStarts["2015-03-28"] = (250,532)
		baselineStarts["2015-04-25"] = (250,532)
		baselineStarts["2015-05-21"] = (268,530)
		baselineStarts["2015-11-13"] = (256,468)
		baselineStarts["2015-11-14"] = (281,491)
		baselineEnds = {}
		baselineEnds["2014-10-09"] = (68,599-252)
		baselineEnds["2015-03-28"] = (68,370)
		baselineEnds["2015-04-25"] = (68,380)
		baselineEnds["2015-05-21"] = (68,342)
		baselineEnds["2015-11-13"] = (68,381)
		baselineEnds["2015-11-14"] = (68,298)
		TBreferences = {}
		TBreferences["2014-10-09"] = (425, 591)
		TBreferences["2015-03-28"] = (425, 591)
		TBreferences["2015-04-25"] = (425, 591)
		TBreferences["2015-05-21"] = (425, 591)
		TBreferences["2015-11-13"] = (425, 591)
		TBreferences["2015-11-14"] = (425, 591)

		# e.g., "2014-10-09" from
		#       "/home/jonathan/q/dissertation/data/2014-10-09/bySlide"
		curdir = os.path.split(os.path.split(os.getcwd())[0])[1]
		#print(curdir)
	
		if curdir in baselineStarts and curdir in TBreferences:
			#baselineStart = (299,599-45)
			#baselineEnd = (68,599-252)
			baselineStart = baselineStarts[curdir]
			baselineEnd = baselineEnds[curdir]
			reference = (baselineStart, baselineEnd)
			TRreference = reference
			TBreference = TBreferences[curdir]
			#TBreference = (425, 591)
		else:
			"ERROR: date dir not found"

		### format = {"TR": {'reference': ((x, y), (x, y)), 'userline': ((x, y), (x, y)), 'intersection': (x, y), 'measurement': x}}
		#fDictDefault = {'TR': {'reference': reference, 'type': 'vector'}, 'TB': {'type': 'point', 'reference': TBreference}}
		self.fDictDefault = {'TR': {'reference': reference, 'type': 'vector'}, 'TB': {'type': 'point', 'reference': TBreference}, 'trace': {'points': [], 'type': 'points'}}
		#Ey4Gekquc2Bv48v
		self.measurementFn = self.filebase+".measurement"
		#colours = {"TR": {"points": "MediumPurple1"}, "TB": {"dots": "lightgreen"}}
		self.colours = {"TR": {"points": "MediumPurple1"}, "TB": {"points": "SeaGreen1", "lines": "SeaGreen2", "references": "SteelBlue1"}, "trace": {"points": "IndianRed"}}

		#image = Image.open(argv[1] if len(argv) >=2 else "018_516.png")
		self.image = tkinter.PhotoImage(file=self.filebase+".png")
		self.canvas = tkinter.Canvas(self, width=self.image.width(), height=self.image.height())
		self.canvas.pack()
		#image_tk = ImageTk.PhotoImage(image)
		self.canvas.create_image(self.image.width()/2, self.image.height()/2, image=self.image)
		self.canvas.create_line(baselineStart[0], baselineStart[1], baselineEnd[0], baselineEnd[1], fill="blue")

		#global fDict
		self.lines = {}
		self.dots = {}
		self.points = {}
		self.references = {}



	def populateList:
		for item in sorted(self.fDict):
			if item != "meta":
				self.listbox.insert(tkinter.END, item)
		self.listbox.selection_set(0)


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

	def writeData(): #fDict):
		with open(self.measurementFn, 'w') as measurementFile:
			measurementFile.write(json.dumps(self.fDict, sort_keys=True, indent=3))
		#print(fDict)

	def loadFile(fn):
		fDict = {}
		if os.path.isfile(fn):
			with open(fn, 'r') as dataFile:
				fileContents = dataFile.read()
			fType = type(json.loads(fileContents))
			# if it's an old-format file:
			if fType == float:
				print("old format file detected")
				measurement = json.loads(fileContents)
				intersection = self.measurement2coordinates(reference[0], reference[1], measurement)
				self.fDict = self.fDictDefault
				self.fDict['TR']['measurement'] = measurement
				self.fDict['TR']['intersection'] = intersection
				self.writeData() #fDict)
			# if it's a new-format file:
			elif fType == dict:
				self.fDict = json.loads(fileContents)
				for elemName in self.fDictDefault:
					if elemName not in self.fDict:
						print("{} not found in data; adding default".format(elemName))
						fDict[elemName] = self.fDictDefault[elemName]
		else:
			self.fDict = self.fDictDefault

	#return fDict

	def onLeftClick(event):
		curMeasure = self.listbox.get(self.listbox.curselection())
		curMeasureType = self.fDict[curMeasure]['type']
		#print(fDict)

		lastClick = self.click	
		self.click = (event.x, event.y)
		#print("clicked at: ", event.x, event.y)
		if curMeasureType == "vector":
			lastDot = self.dots[curMeasure]
			self.dots[curMeasure] = self.canvas.create_oval(event.x-radius, event.y-radius, event.x+radius, event.y+radius, fill='red')
			if lastClick:
				if curMeasure in self.lines:
					self.canvas.delete(self.lines[curMeasure])
				self.lines[curMeasure] = self.canvas.create_line(lastClick[0], lastClick[1], self.click[0], self.click[1], fill='red')
				thislineStart = (lastClick[0], lastClick[1])
				thislineEnd = (self.click[0], self.click[1])
				thisLine = (thislineStart, thislineEnd)
				self.canvas.delete(lastDot)
	
				if curMeasure in self.points:
					self.canvas.delete(self.points[curMeasure])
				intersectionPoint = line_intersection(self.references[curMeasure], thisLine)
				self.points[curMeasure] = self.canvas.create_oval(intersectionPoint[0]-radius, intersectionPoint[1]-radius, intersectionPoint[0]+radius, intersectionPoint[1]+radius, outline=self.colours[curMeasure]["points"])
				#print(intersectionPoint)
				hypotenuse = math.hypot(intersectionPoint[0] - baselineStart[0], intersectionPoint[1] - baselineStart[1])
				#print(hypotenuse)
				self.fDict[curMeasure]['measurement'] = hypotenuse
				self.fDict[curMeasure]['intersection'] = intersectionPoint
				self.fDict[curMeasure]['userline'] = (thislineStart, thislineEnd)
				self.writeData() #self.fDict)
		elif curMeasureType == "point":
			#print(points)
			lastPoint = self.points[curMeasure]
			self.points[curMeasure] = self.canvas.create_oval(event.x-radius, event.y-radius, event.x+radius, event.y+radius, outline=self.colours[curMeasure]["points"])
			#if lastClick:
			if curMeasure in self.lines:
				if self.lines[curMeasure] != None:
					for line in self.lines[curMeasure]:
						self.canvas.delete(line)
			self.canvas.delete(lastPoint)
			self.lines[curMeasure] = (
				self.canvas.create_line(click[0]-50, click[1], click[0]+50, click[1], fill=colours[curMeasure]["lines"]),
				self.canvas.create_line(click[0], click[1]-50, click[0], click[1]+50, fill=colours[curMeasure]["lines"])
			)
			intersectionPoint = (click[0], click[1])
			Dx = self.fDict[curMeasure]['reference'][0] - intersectionPoint[0]
			Dy = self.fDict[curMeasure]['reference'][1] - intersectionPoint[1]
			self.fDict[curMeasure]['intersection'] = intersectionPoint
			self.fDict[curMeasure]['measurement'] = (Dx, Dy)
			self.writeData() #self.fDict)
		#elif curMeasureType == "trace":
		#	#writeData(fDict)
		#	delay_ms=500
		#	time.sleep(delay_ms*0.001)
		#	print("nothing yet")
		elif curMeasureType == "trace":
			traceClicks(events)
	
	def afterLoad():
		# runs after loading the file, displays data from file
		for measure in self.fDict:
			#print(measure)
			#print(fDict[measure]['type'])
			if measure != "meta":
				if self.fDict[measure]['type'] == "vector":
					if "userline" in self.fDict[measure]:
						((x1, y1), (x2, y2)) = self.fDict[measure]['userline']
						self.lines[measure] = self.canvas.create_line(x1, y1, x2, y2, fill='red')
					else:
						self.lines[measure] = None
					if "intersection" in self.fDict[measure]:
						(thisX, thisY) = self.fDict[measure]['intersection']
						self.points[measure] = self.canvas.create_oval(thisX-radius, thisY-radius, thisX+radius, thisY+radius, outline=self.colours[measure]["points"])
					else:
						self.points[measure] = None
					if "reference" in self.fDict[measure]:
						self.references[measure] = self.fDict[measure]['reference']
				elif self.fDict[measure]['type'] == "point":
					if "intersection" in self.fDict[measure]:
						(thisX, thisY) = self.fDict[measure]['intersection']
						self.points[measure] = self.canvas.create_oval(thisX-radius, thisY-radius, thisX+radius, thisY+radius, outline=self.colours[measure]["points"])
						self.lines[measure] = (
							self.canvas.create_line(thisX-50, thisY, thisX+50, thisY, fill=self.colours[measure]["lines"]),
							self.canvas.create_line(thisX, thisY-50, thisX, thisY+50, fill=self.colours[measure]["lines"])
						)
					else:
						self.points[measure] = None
						self.lines[measure] = None
			
					if "reference" in self.fDict[measure]:
						(thisX, thisY) = self.fDict[measure]['reference']
						self.references[measure] = self.canvas.create_oval(thisX-radius, thisY-radius, thisX+radius, thisY+radius, outline=self.colours[measure]["references"])
					else:
						self.references[measure] = None
				elif self.fDict[measure]['type'] == "points":
					print("nothing yet")
		
				self.dots[measure] = None




if __name__ == "__main__":
	app = markingGUI()
	#app.after(500, traceClicks)
	app.mainloop()
