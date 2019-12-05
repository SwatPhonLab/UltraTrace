from .logging import *
from . import *

import numpy as np
import pydicom as dicom
from PIL import Image, ImageTk, ImageEnhance
import tempfile
import matplotlib.pyplot as plt
import zlib
import math
import os

class FrameReader:
	def __init__(self, filename):
		self.filename = filename
		self.data = tempfile.TemporaryFile()
		self.loaded = False

class DicomImgReader(FrameReader):

	label = 'Read pixel data'

	def __init__(self, filename):
		FrameReader.__init__(self, filename)

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

class DicomScanLineReader(FrameReader):

	label = 'Read unannotated'

	def __init__(self, filename):
		FrameReader.__init__(self, filename)
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

class DicomPNGReader(FrameReader):

	label = 'Extract to PNGs'

	def __init__(self, filename):
		FrameReader.__init__(self, filename)
		name = os.path.splitext(os.path.basename(filename))[0]
		self.png_dir = os.path.join(
			os.path.dirname(os.path.abspath(filename)),
			name + '_dicom_to_png'
		)
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
			img = PIL.Image.fromarray( arr )
			img.save(self.png_name % (f+1), format='PNG', compress_level=1)

		self.loaded = True

	def getFrame(self, framenum):
		return Image.open(self.png_name % framenum)

class ULTScanLineReader(FrameReader):

	label = 'Read scan line data'

	def __init__(self, data, metadata):
		pass

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
