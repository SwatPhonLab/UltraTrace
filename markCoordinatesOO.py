#!/usr/bin/env python3

import tkinter
import math
#from sys import argv
import sys
import json
import os
import argparse

class markingGUI(tkinter.Tk):
	def __init__(self):
		tkinter.Tk.__init__(self)

		# require a $PATH and parse it
		parser = argparse.ArgumentParser(description='Process some integers.')
		parser.add_argument('path', help='path (unique to a participant) where subdirectories contain raw data')
		args = parser.parse_args()

		# need to make sure we are given a valid path
		if os.path.exists( args.path ):

			self.path = args.path
			self.metadataFile = os.path.join( self.path, 'metadata.json' )
			self.metadata = self.get_metadata( self.metadataFile )

		else:
			print( "Error locating path: %s" % args.path )
			exit()

		# end progress
		exit()

		# old stuff

		self.setDefaults()

		self.className="mark points: %s" % self.filebase

		self.canvas.bind("<Button-1>", self.onLeftClick)
		self.canvas.bind("<ButtonRelease-1>", self.onLeftUnClick)
		self.canvas.bind("<Motion>", self.onMouseMove)
		self.canvas.bind("<Delete>", self.onDelete)
		self.canvas.bind("<Tab>", self.onDelete)
		self.canvas.bind("<Down>", self.moveDown)
		self.canvas.bind("<Up>", self.moveUp)
		self.canvas.bind("<Left>", self.showPrev)
		self.canvas.bind("<Right>", self.showNext)
		self.canvas.bind("<Button-3>", lambda e: self.destroy())
		self.canvas.bind("<Escape>", lambda e: self.destroy())
		self.canvas.bind("<Button-4>", self.zoomImageOut)
		self.canvas.bind("<Button-5>", self.zoomImageIn)
		self.listbox = tkinter.Listbox(self, height=3, selectmode=tkinter.SINGLE)
		self.listbox.pack()

		# load and process file
		self.loadFile(self.measurementFn)
		self.afterLoad()

		self.populateSelector()
		self.subWindow = self.canvas.create_window((150,90),
			window=self.listbox, anchor="nw")

		self.canvas.focus_set()

	def get_metadata(self, mdfile):
		"""
		opens a metadata file (or creates one if it doesn't exist), recursively searches a directory
			for acceptable files, writes appropriate data back into memory, and returns the metadata object

		acceptable files: the metadata file requires matching files w/in subdirectories based on filenames
			for example, it will try to locate files that have the same base filename and
			each of a set of required extensions
		"""

		# either load up existing metadata
		if os.path.exists( mdfile ):
			print( "loading data from %s" % mdfile )
			with open( mdfile, 'r' ) as f:
				data = json.load( f )

		# or make some new stuff ... no reason to separate these yet at the moment
		#... maybe later on we'll have other types of data stored in here?
		else:
			print( "creating new datafile: %s" % mdfile )
			data = {
				'path': str(self.path),
				'participant': str(os.path.basename( os.path.normpath(self.path) )),
				'alignedFiles': {} }

		# hardcode some required fields
		REQUIRED_FIELDS = { '.dicom', '.flac', '.TextGrid', '.timetag' }
		alignedFiles, unalignedFiles, unaligned = {}, {}, set()

		# now get the objects in subdirectories
		for path, dirs, fs in os.walk( self.path ):
			for f in fs:
				fNoExt, fExt = os.path.splitext( f ) # e.g. 00.dicom -> 00, .dicom
				if fNoExt not in alignedFiles:
					alignedFiles[fNoExt] = {}
				alignedFiles[fNoExt][fExt] = os.path.join( path, f )

		# and align them if they have all of the required filetypes
		# if not, move them to another object `unaligned files`
		for fNoExt in alignedFiles:
			if alignedFiles[fNoExt].keys() != REQUIRED_FIELDS:
				unaligned.add(fNoExt)
		for key in unaligned:
			unalignedFiles[key] = alignedFiles.pop( key )

		# overwrite old data
		data['alignedFiles'] = alignedFiles
		data['unalignedFiles'] = unalignedFiles
		with open( mdfile, 'w' ) as f:
			json.dump( data, f, indent=3 )

		# and return it so that we can keep it in memory
		return data

	def setDefaults(self):
		self.filebase = sys.argv[1]
		print(self.filebase)
		self.radius = 5
		self.click = None

		baselineStarts = {}
		baselineStarts["2014-10-09"] = (299,599-45)
		baselineStarts["2015-03-28"] = (250,532)
		baselineStarts["2015-04-25"] = (250,532)
		baselineStarts["2015-05-21"] = (268,530)
		baselineStarts["2015-11-13"] = (256,468)
		baselineStarts["2015-11-14"] = (281,491)
		baselineStarts["2016-01-20"] = (258,530)
		#baselineStarts["2015-09-10"] = (247,610)
		baselineStarts["2015-09-10"] = (264,529)
		#baselineStarts["2016-02-18"] = (247,613)
		baselineStarts["2016-02-18"] = (277,534)
		#baselineStarts["2016-02-19"] = (254,534) # one dot down
		baselineStarts["2016-02-19"] = (259,501)
		baselineStarts["2016-02-20"] = (272,497)
		baselineStarts["2016-03-16"] = (287,501)
		baselineEnds = {}
		baselineEnds["2014-10-09"] = (68,599-252)
		baselineEnds["2015-03-28"] = (68,370)
		baselineEnds["2015-04-25"] = (68,380)
		baselineEnds["2015-05-21"] = (68,342)
		baselineEnds["2015-11-13"] = (68,381)
		baselineEnds["2015-11-14"] = (68,298)
		baselineEnds["2016-01-20"] = (68,369) # a guess
		#baselineEnds["2015-09-10"] = (67,454) # a guess
		baselineEnds["2015-09-10"] = (67,304) # a guess
		baselineEnds["2016-02-18"] = (67,327) # a guess
		baselineEnds["2016-02-19"] = (67,322) # a guess
		baselineEnds["2016-02-20"] = (67,330) # a guess
		baselineEnds["2016-03-16"] = (67,320) # a guess
		TBreferences = {}
		TBreferences["2014-10-09"] = (425, 591)
		TBreferences["2015-03-28"] = (425, 591)
		TBreferences["2015-04-25"] = (425, 591)
		TBreferences["2015-05-21"] = (425, 591)
		TBreferences["2015-11-13"] = (425, 591)
		TBreferences["2015-11-14"] = (425, 591)
		TBreferences["2016-01-20"] = (425, 591)
		TBreferences["2015-09-10"] = (425, 591)
		TBreferences["2016-02-18"] = (425, 591)
		TBreferences["2016-02-19"] = (425, 591)
		TBreferences["2016-02-20"] = (425, 591)
		TBreferences["2016-03-16"] = (425, 591)

		# e.g., "2014-10-09" from
		#       "/home/jonathan/q/dissertation/data/2014-10-09/bySlide"
		metafn = "dir.metadata"
		newmetafn = os.path.join("bySlide", metafn)
		#print(newmetafn)
		if os.path.exists(metafn):
			with open(metafn, 'r') as metadataFile:
				fileContents = metadataFile.read()
			metadata = json.loads(fileContents)
			curdir = metadata["date"]
		elif os.path.exists(newmetafn):
			with open(newmetafn, 'r') as metadataFile:
				fileContents = metadataFile.read()
			metadata = json.loads(fileContents)
			curdir = metadata["date"]
		else:
			curdirTuple = os.path.split(os.path.split(os.getcwd())[0])
			curdir = curdirTuple[1]
			if curdir not in baselineStarts:
				#last attempt
				curdir = os.path.split(os.path.split(curdirTuple[0])[1])[1]
			#print(curdir)

		if curdir in baselineStarts and curdir in TBreferences:
			#baselineStart = (299,599-45)
			#baselineEnd = (68,599-252)
			self.baselineStart = baselineStarts[curdir]
			self.baselineEnd = baselineEnds[curdir]
			reference = (self.baselineStart, self.baselineEnd)
			TRreference = reference
			TBreference = TBreferences[curdir]
			#TBreference = (425, 591)
		else:
			print("ERROR: date dir OR file to trace not found OR date dir not in TBreferences")
			sys.exit(-1)

		### format = {"TR": {'reference': ((x, y), (x, y)), 'userline': ((x, y), (x, y)), 'intersection': (x, y), 'measurement': x}}
		#fDictDefault = {'TR': {'reference': reference, 'type': 'vector'}, 'TB': {'type': 'point', 'reference': TBreference}}
		self.fDictDefault = {'TR': {'reference': reference, 'type': 'vector'}, 'TB': {'type': 'point', 'reference': TBreference}, 'trace': {'points': [], 'type': 'points'}}
		#Ey4Gekquc2Bv48v
		self.measurementFn = self.filebase+".measurement"
		#colours = {"TR": {"points": "MediumPurple1"}, "TB": {"dots": "lightgreen"}}
		self.colours = {"TR": {"points": "MediumPurple1"}, "TB": {"points": "SeaGreen1", "lines": "SeaGreen2", "references": "SteelBlue1"}, "trace": {"points": "Red"}} #IndianRed"}}

		self.whichImage = "main"
		self.zoomFactor = 2
		self.curZoomFactor = 1
		self.zoomed = False

		#image = Image.open(argv[1] if len(argv) >=2 else "018_516.png")
		self.image = tkinter.PhotoImage(file=self.filebase+".png")
		self.scaledImage = tkinter.PhotoImage(file=self.filebase+".png").zoom(self.zoomFactor)
		self.width = self.image.width()
		self.height = self.image.height()
		self.canvas = tkinter.Canvas(self, width=self.width, height=self.height)
		self.canvas.pack()
		self.references = {}
		#image_tk = ImageTk.PhotoImage(image)
		self.slide = self.canvas.create_image(self.image.width()/2, self.image.height()/2, image=self.image)
		self.makeTRref()

		#global fDict
		self.lines = {}
		self.dots = {}
		self.points = {}
		self.stillClicked = False
		self.curCall = None
		self.paintDelay = 150 # in milliseconds
		self.prevPosition = (0, 0)
		self.distanceBuffer = 8
		self.prevSelection = None

		base = self.filebase.split("_")[0]
		nɛxt = int(self.filebase.split("_")[1])+1
		prev = int(self.filebase.split("_")[1])-1
		nextImageFn = "./adjacent/{}_{}.png".format(base, nɛxt)
		prevImageFn = "./adjacent/{}_{}.png".format(base, prev)
		if os.path.exists(nextImageFn) and os.path.exists(prevImageFn):
			self.nextImage = tkinter.PhotoImage(file=nextImageFn)
			self.prevImage = tkinter.PhotoImage(file=prevImageFn)
			self.nextImageScaled = tkinter.PhotoImage(file=nextImageFn).zoom(self.zoomFactor)
			self.prevImageScaled = tkinter.PhotoImage(file=prevImageFn).zoom(self.zoomFactor)
		else:
			print("WARNING: no previous and/or next frame images!")



	def zoomImageIn(self, event):
		#factor = 2
		if not self.zoomed:
			self.canvas.delete(self.slide)
			#scaledImage = self.image.subsample(2, 2)
			#print(factor)
			#self.scaledImage = tkinter.PhotoImage(file=self.filebase+".png")#.zoom(factor)
			##self.canvas.scale("all", event.x, event.y, factor, factor)
			self.canvas.scale("all", 0, self.height, self.zoomFactor, self.zoomFactor)
			self.slide = self.canvas.create_image(self.image.width()*self.zoomFactor/2, 0, image=self.scaledImage)
			self.canvas.tag_lower(self.slide)
			self.canvas.pack()
			self.zoomed = True
			self.curZoomFactor = self.zoomFactor

		#self.image.scale("all", event.x, event.y, 1.1, 1.1)
		##self.image.zoom(1.1)
		#self.canvas.configure(scrollregion = self.canvas.bbox("all"))

	def zoomImageOut(self, event):
		#factor = 2
		if self.zoomed:
			self.canvas.delete(self.slide)
			self.canvas.scale("all", 0, self.height, 1/self.zoomFactor, 1/self.zoomFactor)
			self.slide = self.canvas.create_image(self.image.width()/2, self.image.height()/2, image=self.image)
			self.canvas.tag_lower(self.slide)
			#self.raiseStuff()
			self.canvas.pack()
			self.zoomed = False
			self.curZoomFactor = 1
		#self.canvas.scale("all", event.x, event.y, 0.9, 0.9)
		##self.image.scale("all", event.x, event.y, 0.9, 0.9)
		#self.canvas.configure(scrollregion = self.canvas.bbox("all"))

	def showNext(self, event):
		if self.whichImage != "next":
			self.canvas.delete(self.slide)
			if self.zoomed:
				self.slide = self.canvas.create_image(self.image.width()*self.zoomFactor/2, 0, image=self.nextImageScaled)
			else:
				self.slide = self.canvas.create_image(self.image.width()/2, self.image.height()/2, image=self.nextImage)

			self.canvas.tag_lower(self.slide)
			self.canvas.pack()
			self.whichImage = "next"
		else:
			self.resetImageToMain()

	def showPrev(self, event):
		if self.whichImage != "prev":
			self.canvas.delete(self.slide)
			if self.zoomed:
				self.slide = self.canvas.create_image(self.image.width()*self.zoomFactor/2, 0, image=self.prevImageScaled)
			else:
				self.slide = self.canvas.create_image(self.image.width()/2, self.image.height()/2, image=self.prevImage)
			self.canvas.tag_lower(self.slide)
			self.canvas.pack()
			self.whichImage = "prev"
		else:
			self.resetImageToMain()

	def resetImageToMain(self):
		self.canvas.delete(self.slide)
		if self.zoomed:
			self.slide = self.canvas.create_image(self.image.width()*self.zoomFactor/2, 0, image=self.scaledImage)
		else:
			self.slide = self.canvas.create_image(self.image.width()/2, self.image.height()/2, image=self.image)
		self.canvas.tag_lower(self.slide)
		self.canvas.pack()
		self.whichImage = "main"


	def makeTRref(self):
		self.references['TR'] = self.canvas.create_line(self.baselineStart[0], self.baselineStart[1], self.baselineEnd[0], self.baselineEnd[1], fill="blue")

	def listChange(self, event):
		#print("focus canvas")
		curMeasure = self.listbox.get(self.listbox.curselection())

		if curMeasure=='trace':
			self.hideStuff()
		else:
			if self.prevSelection=='trace':
				self.unHideStuff()

		self.prevSelection = curMeasure
		self.canvas.focus_set()

	def raiseStuff(self):
		for line in self.lines['TB']:
			self.canvas.tag_raise(line)
		self.canvas.tag_raise(self.lines['TR'])
		self.canvas.tag_raise(self.points['TR'])
		self.canvas.tag_raise(self.points['TB'])
		self.canvas.tag_raise(self.references['TR'])


	def hideStuff(self):
		#print("references", self.references)
		#print("lines", self.lines)
		#print("points", self.points)
		if 'TB' in self.lines:
			if self.lines['TB'] != None:
				for line in self.lines['TB']:
					self.canvas.delete(line)
		#print(self.points)
		self.canvas.delete(self.lines['TR'])
		self.canvas.delete(self.points['TR'])
		self.canvas.delete(self.points['TB'])
		self.canvas.delete(self.references['TR'])

	def unHideStuff(self):
		for measure in ['TR', 'TB']:
			self.makePoint(measure)
			#self.loadPoint(measure)
			#self.loadVector(measure)
			#print(self.fDict)

			#self.points[measure] = self.canvas.create_oval(thisX-self.radius, thisY-self.radius, thisX+self.radius, thisY+self.radius, outline=self.colours[measure]["points"])
		self.makeCrossHairs('TB')
		self.makeReference('TB')
		self.makeTRref()
		self.makeLine('TR')

	def moveDown(self, event):
		self.listbox.focus_set()
		current = self.listbox.curselection()[0]
		total = self.listbox.size()
		#print(current,total)
		if total > current+1:
			self.listbox.selection_clear(current)
			#self.listbox.activate(current + 1)
			#self.listbox.selection_set(0)
			self.listbox.selection_set(current + 1)
		#self.canvas.focus_set()

	def moveUp(self, event):
		self.listbox.focus_set()
		current = self.listbox.curselection()[0]
		if current > 0:
			self.listbox.selection_clear(current)
			#self.listbox.activate(current - 1)
			#self.listbox.selection_set(0)
			self.listbox.selection_set(current - 1)
		#self.canvas.focus_set()

	def populateSelector(self):
		for item in sorted(self.fDict):
			if item != "meta":
				self.listbox.insert(tkinter.END, item)
		self.listbox.selection_set(0)
		#self.listbox.bind('<<ListboxSelect>>', self.listChange)
		self.listbox.bind('<ButtonRelease-1>', self.listChange)
		self.listbox.bind('<KeyRelease>', self.listChange)


	def line_intersection(self, line1, line2):
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


	def measurement2coordinates(self, source, end, distance):
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

	def writeData(self): #fDict):
		with open(self.measurementFn, 'w') as measurementFile:
			measurementFile.write(json.dumps(self.fDict, sort_keys=True, indent=3))
		#print(fDict)

	def loadFile(self, fn):
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
						self.fDict[elemName] = self.fDictDefault[elemName]
		else:
			self.fDict = self.fDictDefault

	#return fDict

	def vectorClick(self, event, curMeasure, lastClick):
		lastDot = self.dots[curMeasure]
		self.dots[curMeasure] = self.canvas.create_oval(event.x-self.radius, event.y-self.radius, event.x+self.radius, event.y+self.radius, fill='red')
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
			intersectionPoint = self.line_intersection(self.references[curMeasure], thisLine)
			self.points[curMeasure] = self.canvas.create_oval(intersectionPoint[0]-self.radius, intersectionPoint[1]-self.radius, intersectionPoint[0]+self.radius, intersectionPoint[1]+self.radius, outline=self.colours[curMeasure]["points"])
			#print(intersectionPoint)
			hypotenuse = math.hypot(intersectionPoint[0] - self.baselineStart[0], intersectionPoint[1] - self.baselineStart[1])
			#print(hypotenuse)
			self.fDict[curMeasure]['measurement'] = hypotenuse
			self.fDict[curMeasure]['intersection'] = intersectionPoint
			self.fDict[curMeasure]['userline'] = (thislineStart, thislineEnd)
			self.writeData() #self.fDict)

	def pointClick(self, event, curMeasure, lastClick):
		#print(points)
		#true_x = self.canvas.canvasx(event.x)
		#true_y = self.canvas.canvasy(event.y)
		#true_x = event.x/2
		#true_y = event.y/2
		#print(event.x, event.y)
		#print(true_x, true_y)
		lastPoint = self.points[curMeasure]
		self.points[curMeasure] = self.canvas.create_oval(event.x-self.radius*self.curZoomFactor, event.y-self.radius*self.curZoomFactor, event.x+self.radius*self.curZoomFactor, event.y+self.radius*self.curZoomFactor, outline=self.colours[curMeasure]["points"])
		#if lastClick:
		if curMeasure in self.lines:
			if self.lines[curMeasure] != None:
				for line in self.lines[curMeasure]:
					self.canvas.delete(line)
		self.canvas.delete(lastPoint)
		self.lines[curMeasure] = (
			self.canvas.create_line(event.x-50*self.curZoomFactor, event.y, event.x+50*self.curZoomFactor, event.y, fill=self.colours[curMeasure]["lines"]),
			self.canvas.create_line(event.x, event.y-50*self.curZoomFactor, event.x, event.y+50*self.curZoomFactor, fill=self.colours[curMeasure]["lines"])
		)
		intersectionPoint = (self.click[0], self.click[1])
		Dx = self.fDict[curMeasure]['reference'][0] - intersectionPoint[0]
		Dy = self.fDict[curMeasure]['reference'][1] - intersectionPoint[1]
		self.fDict[curMeasure]['intersection'] = intersectionPoint
		self.fDict[curMeasure]['measurement'] = (Dx, Dy)
		self.writeData() #self.fDict)

	#def traceClicks(self, event, curMeasure, lastClick):
	#	print("tracing?")
	#
	#	if self.stillClicked:
	#		print("hargle")
	#		#self.after(500, self.traceClicks(event, curMeasure, lastClick))

	def onMouseMove(self, event):
		if self.zoomed:
			self.click = (event.x/2, (self.height+event.y)/2)
		else:
			self.click = (event.x, event.y)

		if self.stillClicked:
			curPosition = self.click #(event.x, event.y)
			Dx = abs(event.x - self.prevPosition[0]) #*self.curZoomFactor
			Dy = abs(event.y - self.prevPosition[1]) #*self.curZoomFactor
			#print(Dx, Dy)
			if Dx > self.distanceBuffer*self.curZoomFactor or Dy > self.distanceBuffer*self.curZoomFactor:
				thisDiamond = self.create_diamond((event.x, event.y))
				#self.canvas.create_oval(event.x-self.radius, event.y-self.radius, event.x+self.radius, event.y+self.radius, fill='red')
				self.points['trace'].append(thisDiamond)
				self.references['trace'][thisDiamond] = curPosition
				self.fDict['trace']['points'].append(curPosition)  # FIXME: but different if zoomed
				self.writeData()
				self.prevPosition = (event.x, event.y)


	def create_diamond(self, centre):
		#print(centre)
		return self.canvas.create_polygon(centre[0]-self.radius*self.curZoomFactor, centre[1], centre[0], centre[1]+self.radius*self.curZoomFactor, centre[0]+self.radius*self.curZoomFactor, centre[1], centre[0], centre[1]-self.radius*self.curZoomFactor, fill='', outline=self.colours['trace']['points'])

	#def trackClicked(self, event):
		#print("tracing")
		#
		#if self.stillClicked:
		#	curPosition = (event.x, event.y)
		#	Dx = abs(curPosition[0] - self.prevPosition[0])
		#	Dy = abs(curPosition[1] - self.prevPosition[1])
		#	print(Dx, Dy)
		#	if Dx > self.distanceBuffer or Dy > self.distanceBuffer:
		#		self.canvas.create_oval(event.x-self.radius, event.y-self.radius, event.x+self.radius, event.y+self.radius, fill='red')
		#
		#	self.prevPosition = curPosition
		#	#self.curCall = self.after(self.paintDelay, self.trackClicked, event)

	def onLeftUnClick(self, event):
		self.stillClicked = False
		self.prevPosition = (0, 0)
		if self.curCall != None:
			self.after_cancel(self.curCall)

	def onDelete(self, event):
		curMeasure = self.listbox.get(self.listbox.curselection())
		curMeasureType = self.fDict[curMeasure]['type']

		if curMeasureType == "points":
			#print(self.references)
			if len(self.points['trace'])>=1:
				toDelete = self.points['trace'][-1]
				toDeletePt = self.references['trace'][toDelete]
				#print(toDelete)
				self.canvas.delete(toDelete)
				del self.points['trace'][-1]
				#print(toDeletePt)
				self.fDict['trace']['points'].remove(toDeletePt)
				self.writeData()

	def onLeftClick(self, event):
		curMeasure = self.listbox.get(self.listbox.curselection())
		curMeasureType = self.fDict[curMeasure]['type']
		#print(fDict)

		lastClick = self.click
		if self.zoomed:
			self.click = (event.x/2, (self.height+event.y)/2)
		else:
			self.click = (event.x, event.y)
		#print("clicked at: ", event.x, event.y)
		if curMeasureType == "vector":
			self.vectorClick(event, curMeasure, lastClick)

		elif curMeasureType == "point":
			self.pointClick(event, curMeasure, lastClick)

		#elif curMeasureType == "trace":
		#	#writeData(fDict)
		#	delay_ms=500
		#	time.sleep(delay_ms*0.001)
		#	print("nothing yet")
		elif curMeasureType == "points":
			self.stillClicked = True
			#self.traceClicks(event, curMeasure, lastClick)
			self.onMouseMove(event)

		else:
			print("undefined: {}".format(curMeasureType))

	def loadVector(self, measure):
		if "userline" in self.fDict[measure]:
			#print("BLER", measure)
			self.makeLine(measure)

		else:
			self.lines[measure] = None
		if "intersection" in self.fDict[measure]:
			(thisX, thisY) = self.fDict[measure]['intersection']
			self.points[measure] = self.canvas.create_oval(thisX-self.radius, thisY-self.radius, thisX+self.radius, thisY+self.radius, outline=self.colours[measure]["points"])
		else:
			self.points[measure] = None
		#if "reference" in self.fDict[measure]:
			#print("measure", measure)
			##self.references[measure] = self.fDict[measure]['reference']
			#self.references[measure] = "HARGLE" #self.fDict[measure]['reference']

	def makeReference(self, measure):
		#print("ref {}".format(measure))
		#print(self.fDict[measure]["reference"])
		(thisX, thisY) = self.fDict[measure]["reference"]
		self.references[measure] = self.canvas.create_oval(thisX-self.radius, thisY-self.radius, thisX+self.radius, thisY+self.radius, outline=self.colours[measure]["references"])

	def makePoint(self, measure):
		#if measure=="TB":
		#	hargle = "intersection"
		#	bargle = "points"
		#elif measure=="TR":
		#	hargle = "reference"
		#	bargle = "references"

		(thisX, thisY) = self.fDict[measure]["intersection"]
		#print(thisX, thisY, self.radius)
		self.points[measure] = self.canvas.create_oval(thisX-self.radius, thisY-self.radius, thisX+self.radius, thisY+self.radius, outline=self.colours[measure]["points"])

	def makeCrossHairs(self, measure):
		(thisX, thisY) = self.fDict[measure]["intersection"]
		self.lines[measure] = (
			self.canvas.create_line(thisX-50, thisY, thisX+50, thisY, fill=self.colours[measure]["lines"]),
			self.canvas.create_line(thisX, thisY-50, thisX, thisY+50, fill=self.colours[measure]["lines"])
		)
		#print("TB lines", self.lines['TB'])

	def makeLine(self, measure):
		if "userline" in self.fDict[measure]:
			((x1, y1), (x2, y2)) = self.fDict[measure]['userline']
			self.lines[measure] = self.canvas.create_line(x1, y1, x2, y2, fill='red')

	def loadPoint(self, measure):
		#print("loadPoint", measure, self.fDict[measure])
		#print(self.colours)
		if "intersection" in self.fDict[measure]:
			#if "lines" in self.colours[measure]:
			self.makePoint(measure)
#			(thisX, thisY) = self.fDict[measure]['intersection']
#			self.points[measure] = self.canvas.create_oval(thisX-self.radius, thisY-self.radius, thisX+self.radius, thisY+self.radius, outline=self.colours[measure]["points"])
			self.makeCrossHairs(measure)
#			self.lines[measure] = (
#				self.canvas.create_line(thisX-50, thisY, thisX+50, thisY, fill=self.colours[measure]["lines"]),
#				self.canvas.create_line(thisX, thisY-50, thisX, thisY+50, fill=self.colours[measure]["lines"])
#			)
		else:
			self.points[measure] = None
			self.lines[measure] = None

		if "reference" in self.fDict[measure]:
			self.makeReference(measure)
#			(thisX, thisY) = self.fDict[measure]['reference']
#			#print(thisX, thisY, self.radius)
#			self.references[measure] = self.canvas.create_oval(thisX-self.radius, thisY-self.radius, thisX+self.radius, thisY+self.radius, outline=self.colours[measure]["references"])
		else:
			self.references[measure] = None

	def loadPoints(self, measure):
		self.references[measure] = {}
		self.points[measure] = []
		for tracePt in self.fDict[measure]['points']:
			thisDiamond = self.create_diamond(tracePt)
			#self.references[measure]
			#if measure not in self.references:
			#
			if thisDiamond in self.references:
				print("¡PELIGRO!")
			self.references[measure][thisDiamond] = tracePt
			self.points[measure].append(thisDiamond)

	def afterLoad(self):
		# runs after loading the file, displays data from file
		for measure in self.fDict:
			#print(measure)
			#print(fDict[measure]['type'])
			if measure != "meta":
				#print(measure)
				if self.fDict[measure]['type'] == "vector":
					self.loadVector(measure)
				elif self.fDict[measure]['type'] == "point":
					self.loadPoint(measure)
				elif self.fDict[measure]['type'] == "points":
					self.loadPoints(measure)
				self.dots[measure] = None
				#print(self.references, self.points, self.lines, self.dots, measure)




if __name__ == "__main__":
	app = markingGUI()
	#app.after(500, traceClicks)
	#app.after(500, app.trackClicked)
	app.mainloop()
