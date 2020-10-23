from .logging import *
from . import printProgressBar

from abc import ABC, abstractmethod

import numpy as np
import pydicom as dicom
from PIL import Image, ImageTk, ImageEnhance
import tempfile
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
import zlib
import math
import os

class FrameReader(ABC):
	def __init__(self, filename):
		self.filename = filename
		self.data = tempfile.TemporaryFile()
		self.loaded = False

	@abstractmethod
	def load(self):
		pass

	@abstractmethod
	def getFrame(self, framenum):
		pass

	@abstractmethod
	def getFrameTimes(self):
		pass

class DicomReader(FrameReader):
	def getFrameTimes(self):
		dcm = dicom.read_file(self.filename, stop_before_pixels=True)
		try:
			blob = dcm[0x200d,0x3cf4][0][0x200d,0x3cf1][0]
			headers = blob[0x200d,0x3cfb].value
			offset = float(int.from_bytes(headers[:4], byteorder='little')) / 1000000
			return [float(int.from_bytes(headers[i:i+4], byteorder='little')) / 1000000 - offset for i in range(0, len(headers), 32)]
		except:
			frametime = dcm.get('FrameTime')
			numframes = dcm.get('NumberOfFrames')
			return [float(i * frametime) / 1000 for i in range(numframes)]

	def load(self):
		pass

	def getFrame(self, framenum):
		pass

class DicomImgReader(DicomReader):

	label = 'Read pixel data'

	def __init__(self, filename):
		DicomReader.__init__(self, filename)

	def load(self):
		debug('DicomImgReader: reading dicom')
		dcm = dicom.read_file(self.filename)
		debug('DicomImgReader: copying pixels')
		pixels = dcm.pixel_array
		del dcm
		self.RGB = (len(pixels.shape) == 4)
		if self.RGB and pixels.shape[0] == 3:
			debug('DicomImgReader: reshaping pixels')
			pixels = pixels.reshape(pixels.shape[1:] + [3])
		debug('DicomImgReader: dumping pixels')
		pixels.tofile(self.data)
		self.shape = pixels.shape
		del pixels
		self.frame_size = self.shape[1] * self.shape[2]
		if self.RGB:
			self.dtype = np.dtype(('uint8', (self.shape[1], self.shape[2], self.shape[3])))
			self.frame_size *= 3
		else:
			self.dtype = np.dtype(('uint8', (self.shape[1], self.shape[2])))
		self.loaded = True

	def getFrame(self, framenum):
		self.data.seek(self.frame_size * (framenum-1))
		buf = self.data.read(self.frame_size)
		data = np.ndarray(shape=self.shape[1:], buffer=buf, dtype='uint8')
		return Image.fromarray(data)

class DicomScanLineReader(DicomReader):

	label = 'Read unannotated'

	def __init__(self, filename):
		DicomReader.__init__(self, filename)
		dcm = dicom.read_file(self.filename, stop_before_pixels=True)
		blob = dcm[0x200d,0x3cf4][0][0x200d,0x3cf1][0]
		headers = blob[0x200d,0x3cfb].value
		data = blob[0x200d,0x3cf3].value
		framecount = int.from_bytes(data[4:8], byteorder='little')
		offsets = [int.from_bytes(data[i*4+8:i*4+12], byteorder='little') for i in range(framecount)]
		offsets.append(len(data))
		self.frames = []
		for frame in range(framecount):
			framedata = data[offsets[frame]:offsets[frame+1]]
			dt = zlib.decompress(framedata[32:])
			sh = (368, 712)
			arr = np.ndarray(shape=sh, buffer=dt, dtype='uint8')
			arr = np.flip(arr, (0,1))
			self.frames.append(arr)
		self.loaded = True

	def load(self):
		pass

	def getFrame(self, framenum):
		return Image.fromarray(self.frames[framenum-1], 'L')

class DicomPNGReader(DicomReader):

	label = 'Extract to PNGs'

	def __init__(self, filename, png_dir=None):
		DicomReader.__init__(self, filename)
		name = os.path.splitext(os.path.basename(filename))[0]
		if png_dir:
			dr = os.path.abspath(png_dir)
		else:
			dr = os.path.dirname(os.path.abspath(png_dir or filename))
		self.png_dir = os.path.join(dr, name + '_dicom_to_png')
		info(self.png_dir)
		self.png_name = os.path.join(self.png_dir, name + '_frame_%04d.png')
		self.loaded = os.path.exists(self.png_dir)

	def load(self):
		os.mkdir(self.png_dir)
		info( 'Reading DICOM data ...', end='\r' )
		dcm = dicom.read_file(self.filename)
		pixels = dcm.pixel_array

		# check encoding, manipulate array if we need to
		if len(pixels.shape) == 3:      # greyscale
			RGB = False
			frames, rows, columns = pixels.shape
		elif len(pixels.shape) == 4:    # RGB-encoded
			RGB = True
			if pixels.shape[0] == 3:    # handle RGB-first
				rgb, frames, rows, columns = pixels.shape
			else:                       # and RGB-last
				frames, rows, columns, rgb = pixels.shape
			pixels = pixels.reshape([ frames, rows, columns, rgb ])

		printProgressBar(0, frames, prefix = 'Processing:', suffix = 'complete')
		for f in range(frames):
			printProgressBar(f+1, frames, prefix = 'Processing:', suffix = ('complete (%d of %d)' % (f+1,frames)))
			arr = pixels[ f,:,:,: ] if RGB else pixels[ f,:,: ]
			img = Image.fromarray( arr )
			img.save(self.png_name % (f+1), format='PNG', compress_level=1)

		self.loaded = True

	def getFrame(self, framenum):
		try:
			return Image.open(self.png_name % framenum)
		except FileNotFoundError:
			error('file %s does not exist' % (self.png_name % framenum))
			return None

class ULTScanLineReader(FrameReader):

	label = 'Read scan line data'

	def __init__(self, data, metadata):
		FrameReader.__init__(self, data)
		#f = open(data, 'rb')
		#self.data.write(f.read())
		#f.close()
		self.data = open(data, 'rb')
		# sometimes copying to a temporary file misses things
		# however, if we do this it might not get closed
		f = open(metadata)
		for l in f.readlines():
			k, v = l.strip().split('=')
			if ',' in v or '.' in v:
				self.__dict__[k] = float(v.replace(',', '.'))
			else:
				self.__dict__[k] = int(v)
		f.close()
		self.loaded = True
		self.radspace = np.linspace(self.ZeroOffset, self.ZeroOffset+self.PixPerVector, num=self.PixPerVector)
		total = self.Angle * self.NumVectors
		self.thetaspace = np.linspace((math.pi + total) / 2, (math.pi - total) / 2, num=self.NumVectors)
		self.FrameSize = self.NumVectors * self.PixPerVector
		self.data.seek(0, os.SEEK_END)
		self.FrameCount = self.data.tell() // self.FrameSize

	def load(self):
		raise NotImplementedError()

	def getFrame(self, framenum):
		self.data.seek(max(self.FrameSize * (framenum - 1), 0))
		byt = self.data.read(self.FrameSize)
		data = np.ndarray(shape=(self.NumVectors, self.PixPerVector), buffer=byt, dtype='uint8').swapaxes(0,1)
		fig = plt.figure()
		fig.patch.set_facecolor('black')
		ax = fig.add_subplot(111, polar='True')
		ax.axis('off')
		ax.set_thetamin(0)
		ax.set_thetamax(180)
		ax.pcolormesh(self.thetaspace, self.radspace, data, cmap='gray')
		canvas = FigureCanvasAgg(fig)
		canvas.draw()
		r = self.ZeroOffset+self.PixPerVector
		px = ax.transData.transform([[0,0], [math.pi/2, r], [self.thetaspace[0], r], [self.thetaspace[-1], r]])
		xmin = math.floor(px[2][0])
		xmax = math.ceil(px[3][0])
		ymin = math.floor(px[0][1])
		ymax = math.ceil(px[1][1])
		ret = Image.frombytes('RGB', canvas.get_width_height(), canvas.tostring_rgb())
		plt.close(fig)
		return ret.crop((xmin, ymin, xmax, ymax))

	def getFrameTimes(self):
		inc = 1.0 / self.FramesPerSec
		return [self.TimeInSecsOfFirstFrame + i * inc for i in range(self.FrameCount)]

READERS = {
	'dicom': [DicomImgReader, DicomScanLineReader, DicomPNGReader],
	'ult': [ULTScanLineReader],
	None: []
}

LABEL_TO_READER = {}
for k in READERS:
	LABEL_TO_READER[k] = {}
	for cls in READERS[k]:
		LABEL_TO_READER[k][cls.label] = cls
