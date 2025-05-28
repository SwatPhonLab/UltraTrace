#!/usr/bin/env python3

import json
import argparse
import wave
import contextlib
import os

from textgrid import TextGrid, PointTier, Point

class Object:
	pass

def getLengthWav(wavfile):
	with contextlib.closing(wave.open(wavfile,'r')) as f:
		frames = f.getnframes()
		rate = f.getframerate()
		duration = frames / float(rate)
		#print(duration)
	return duration

def getUSdata(USfn):
	data = Object()
	with open(USfn, 'r') as USfile:
		for line in USfile.readlines():
			k, v = line.strip().split('=')
			if "," in v or "." in v:
				data.__dict__[k] = float(v.replace(',', '.'))
			else:
				data.__dict__[k] = int(v)

	#		if "FramesPerSec" in line:
	#			(field, fps) = line.split("=")
	#		elif "TimeInSecsOfFirstFrame" in line:
	#			(field, firstFrame) = line.split("=")
	#	fps = float(fps.replace(",", "."))
	#	firstFrame = float(firstFrame.replace(",", "."))
	#return (fps, firstFrame)
	return data

def createTextGrid(tgfn, name, maxtime, firstFrame, numFrames, fps):
	tg = TextGrid(name=name, maxTime=maxtime)

	pt = PointTier(name="frames", maxTime=maxtime)
	#print(maxtime)
	for frame in range(0,numFrames):
		#print(frame, firstFrame, firstFrame+(frame*(1/fps)))
		pt.add(firstFrame+(frame*(1/fps)), str(frame))
	
	tg.append(pt)

	with open(tgfn, 'w') as tg_file:
		tg.write(tg_file)

#        cls.tg = textgrid.TextGrid.fromFile('test_double_quotes.TextGrid')
#
#        cls.tg.write('test_double_quotes_tg.TextGrid')
#        cls.tg[0].write('test_double_quotes_it.IntervalTier')
#        cls.tg[1].write('test_double_quotes_pt.PointTier')

def getNumFrames(data, ultfn):
	rawult = open(ultfn, 'rb')
	rawult.seek(0, os.SEEK_END)
	frameSize = data.NumVectors * data.PixPerVector
	#print(frameSize, rawult.tell())
	numFrames = rawult.tell() // frameSize
	rawult.close()
	#print(numFrames)
	return numFrames


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("filename", type=str, help="metadata file")

	args = parser.parse_args()


	dirname = os.path.dirname(args.filename)
	with open(args.filename, 'r') as file:
		metadata = json.load(file)
		for fileset in metadata['files']:
			if 'US.txt' in fileset and '.wav' in fileset and '.TextGrid' not in fileset:
				#print(fileset['US.txt'])
				wavlength = getLengthWav(os.path.join(dirname, fileset['.wav']))
				data = getUSdata(os.path.join(dirname, fileset['US.txt']))
				data.firstFrame = data.TimeInSecsOfFirstFrame
				data.fps = data.FramesPerSec
				numFrames = getNumFrames(data, os.path.join(dirname, fileset['.ult']))
				lengthByFrames = numFrames / data.fps
				maxtime = max(wavlength, lengthByFrames) + data.firstFrame + 1.5*(1/data.fps) # adding 1.5 frames "just-in-case" as padding
				#print(maxlength)
				tgfn = os.path.join(dirname, fileset['name']+".TextGrid")
				createTextGrid(tgfn, fileset['name'], maxtime, data.firstFrame, numFrames, data.fps)
