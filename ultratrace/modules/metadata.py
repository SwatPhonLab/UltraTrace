from .base import Module
from ..util.logging import *
from .. import util

import json
import os
import math

from tkinter import filedialog
from magic import Magic # python-magic

class Metadata(Module):
    def __init__(self, app, path):
        '''
        opens a metadata file (or creates one if it doesn't exist), recursively searches a directory
            for acceptable files, writes metadata back into memory, and returns the metadata object

        acceptable files: the metadata file requires matching files w/in subdirectories based on filenames
            for example, it will try to locate files that have the same base filename and
            each of a set of required extensions
        '''
        info( ' - initializing module: Data')
        if path == None:
            app.update()
            path = filedialog.askdirectory(initialdir=os.getcwd(), title="Choose a directory")
            if not path:
                error("No directory chosen - exiting")
                exit(1)

        debug( '   - parsing directory: `%s`' % path )

        if os.path.exists( path ) == False:
            severe( "   - ERROR: `%s` could not be located" % path )
            exit(1)

        self.app = app
        self.path = path

        self.mdfile = os.path.join( self.path, 'metadata.json' )

        # either load up existing metadata
        if os.path.exists( self.mdfile ):
            debug( "   - found metadata file: `%s`" % self.mdfile )
            with open( self.mdfile, 'r' ) as f:
                self.data = json.load( f )

        # or create new stuff
        else:
            if "trace.old files exist":
                "read the files"

            self.path = os.path.abspath(self.path)
            debug( "   - creating new metadata file: `%s`" % self.mdfile )
            self.data = {
                'firstrun_path': self.path,
                'defaultTraceName': 'tongue',
                'traces': {
                    'tongue': {
                        'color': 'red',
                        'files': {} } },
                'offset':0,
                'files': {} }

            # we want each object to have entries for everything here
            fileKeys = { '_prev', '_next', 'processed', 'offset' } # and `processed`
            MIMEs = {
                'audio/x-wav'       :   ['.wav'],
                'audio/x-flac'      :   ['.flac'],
                'audio/wav'     :   ['.wav'],
                'audio/flac'        :   ['.flac'],
                'application/dicom' :   ['.dicom'],
                'text/plain'        :   ['.TextGrid', 'US.txt', '.txt', '.dat'],
                'application/octet-stream' : ['.ult'],
                'application/x-dosexec'    : ['.ult']
            }
            files = {}

            splines = None

            # now get the objects in subdirectories
            for path, dirs, fs in os.walk( self.path ):
                for f in fs:
                    # exclude some filetypes explicitly here by MIME type
                    filepath = os.path.join( path, f )
                    filename, extension = os.path.splitext( f )

                    # allow us to follow symlinks
                    real_filepath = os.path.realpath(filepath)

                    #make file path relative to metadata file
                    filepath = os.path.relpath(filepath,start=self.path)

                    mime_type = Magic(mime=True).from_file(real_filepath)

                    # name mangling for ULT directories
                    if mime_type == 'text/plain' and extension == '.txt' and filename.endswith('US'):
                        filename = filename[:-2]
                        extension = 'US.txt'
                    if extension == '.wav' and filename.endswith('_Track0'):
                        filename = filename[:-7]
                    elif extension == '.wav' and (filename.endswith('_Track1') or filename.endswith('_Track2')):
                        continue
                    elif extension == '.dat' and filename == 'SPLINES':
                        splines = filepath
                        continue

                    if (mime_type == 'text/plain' or mime_type == 'application/json') and extension == '.measurement':
                        debug('Found old measurement file {}'.format(filename))
                        self.importOldMeasurement(real_filepath, filename)
                    elif mime_type in MIMEs:
                        # add `good` files
                        if extension in MIMEs[ mime_type ]:
                            if filename not in files:
                                files[filename] = { key:None for key in fileKeys }
                            files[filename][extension] = filepath
                    elif mime_type == 'image/png' and '_dicom_to_png' in path:
                        # check for preprocessed dicom files
                        name, frame = filename.split( '_frame_' )
                        #debug(files)
                        # if len(files) > 0:
                        # might be able to combine the following; check
                        if name not in files:
                            files[name] = {'processed': None}
                        if files[name]['processed'] == None:
                            files[name]['processed'] = {}
                        files[name]['processed'][str(int(frame))] = filepath

            # check that we find at least one file
            if len(files) == 0:
                severe( '   - ERROR: `%s` contains no supported files' % path )
                exit()

            # sort the files so that we can guess about left/right ... extrema get None/null
            # also add in the "traces" bit here
            _prev = None
            for key in sorted( files.keys() ):
                if _prev != None:
                    files[_prev]['_next'] = key
                files[key]['_prev'] = _prev
                _prev = key
                files[key]['name'] = key

            # sort files, set the geometry, and write
            self.data[ 'files' ] = [ files[key] for key in sorted(files.keys()) ]
            self.data[ 'geometry' ] = '1150x800+1400+480'

            if splines != None:
                self.importULTMeasurement(splines)

            self.write()

        self.app.geometry( self.getTopLevel('geometry') )
        self.files = self.getFilenames()

    def importOldMeasurement(self, filepath, filename):
        '''
        Writes information from .measurement file into metadata file
        '''
        #this is a hack -- should really go into Dicom (which is not yet loaded) and check
        defaultx = 800
        defaulty = 600

        open_file = json.load(open(filepath, 'r'))
        for key, value in open_file.items():
            if isinstance(value, dict):
                if 'type' in value.keys() and 'points' in value.keys():
                    array = value['points']

        filenum, framenum = filename.split('_')
        # new_array = [{"x":point1/800,"y":point2/600} for point1, point2 in array]
        new_array = []
        for point1, point2 in array:
            #assuming traces were made at 1x zoom and no pan
            el = {"x":point1/defaultx,"y":point2/defaulty} #converts coords to "true" (i.e. % through each axis),
            new_array.append(el)
        list_of_files = self.data['traces']['tongue']['files']
        if not filenum in list_of_files:
            list_of_files[filenum]={}
        list_of_files[filenum][framenum] = new_array

    def importULTMeasurement(self, filepath):
        from ..util.framereader import ULTScanLineReader
        f = open(self.unrelativize(filepath), 'rb')
        contents = util.decode_bytes(f.read())
        f.close()
        data = [x.split('\t') for x in contents.splitlines()]
        lines = []
        coords_loc = {}
        confidence_loc = {}
        offset = 3
        defaultTrace = None
        for col in data[0][3:]:
            name = col.split('"')[1]
            if col.startswith('X,Y'):
                coords_loc[name] = offset
                offset += 84
                if not defaultTrace:
                    defaultTrace = name
            elif col.startswith('Confidence'):
                confidence_loc[name] = offset
                offset += 42
        if defaultTrace:
            self.data['defaultTraceName'] = defaultTrace
        for linenum, line in enumerate(data[1:], start=2):
            dt = {}
            for k in coords_loc:
                conf = [100]*42
                if k in confidence_loc:
                    offset = confidence_loc[k]
                    for i in range(42):
                        if line[i+offset]: conf[i] = int(line[i+offset])
                pts = []
                offset = coords_loc[k]
                for i in range(42):
                    xs = line[(2*i)+offset]
                    ys = line[(2*i)+offset+1]
                    if xs and ys and conf[i] > 50:
                        pts.append((float(xs.replace(',', '.')), float(ys.replace(',', '.'))))
                if pts:
                    dt[k] = pts
            if dt:
                lines.append((linenum, float(line[1].replace(',', '.')), line[2], dt))
        self.data['traces'] = {k: {'color': 'red', 'files': {}} for k in coords_loc}
        # TODO: all traces are imported as the same color
        for linenum, timestamp, date, data in lines:
            for fblob in self.data['files']:
                if '.txt' not in fblob or '.ult' not in fblob or 'US.txt' not in fblob:
                    continue
                f = open(self.unrelativize(fblob['.txt']), 'rb')
                byt = f.read()
                f.close()
                s = ''
                for enc in ['utf-8', 'Windows-1251', 'Windows-1252', 'ISO-8859-1']:
                    try:
                        s = byt.decode(enc)
                        break
                    except:
                        pass
                if date in s:
                    reader = ULTScanLineReader(self.unrelativize(fblob['.ult']), self.unrelativize(fblob['US.txt']))
                    ts = reader.getFrameTimes()
                    framenum = 0
                    for i in range(len(ts)):
                        if ts[i] >= timestamp:
                            framenum = i-1
                            break
                    height = (reader.PixPerVector + reader.ZeroOffset) / reader.PixelsPerMm
                    width = 2*math.cos((math.pi/2) - (reader.Angle * reader.NumVectors/2))*height
                    for k in data:
                        if fblob['name'] not in self.data['traces'][k]['files']:
                            self.data['traces'][k]['files'][fblob['name']] = {}
                        conv = []
                        for pt in data[k]:
                            conv.append({'x': pt[0] / width, 'y': 1 - (pt[1] / height)})
                        self.data['traces'][k]['files'][fblob['name']][str(framenum)] = conv
                    info('Line %s of %s imported as %s frame %s' % (linenum, filepath, fblob['name'], framenum))
                    break
            else:
                warn('Unable to import line %s of %s (could not match date %s)' % (linenum, filepath, date))

    def write(self, _mdfile=None):
        '''
        Write metadata out to file
        '''
        # debug(self.data, 'write')
        mdfile = self.mdfile if _mdfile==None else _mdfile
        with open( mdfile, 'w' ) as f:
            json.dump( self.data, f, indent=3 )

    def getFilenames( self ):
        '''
        Returns a list of all the files discovered from the initial directory traversal
        '''
        return [ f['name'] for f in self.data['files'] ]

    def getPreprocessedDicom( self, _frame=None ):
        '''
        Gets preprocessed (.dicom->.png) picture data for a given frame
        '''
        frame = self.app.frame if _frame==None else _frame #int(_frame)-1
        processed = self.getFileLevel( 'processed' )
        try:
            return self.unrelativize(processed[str(frame)])
        except Exception as e: # catches missing frames and missing preprocessed data
            error(e)
            return None

    def getTopLevel( self, key ):
        '''
        Get directory-level metadata
        '''
        if key in self.data.keys():
            return self.data[key]
        else:
            return None

    def setTopLevel( self, key, value ):
        '''
        Set directory-level metadata
        '''
        self.data[ key ] = value
        self.write()

    def getFileLevel( self, key, _fileid=None ):
        '''
        Get file-level metadata
        '''
        fileid = self.app.currentFID if _fileid==None else _fileid
        mddict = self.data[ 'files' ][ fileid ]

        if key == 'all':
            return mddict.keys()
        elif key in mddict and mddict[ key ] != None:
            # if type(mddict[key]) is dict:
            #   for el in mddict[key].keys():
            #       mddict[key][el] = os.path.join(self.path, mddict[key][el])
            # else:
            #   mddict[key] = os.path.join(self.path, mddict[key])
            # debug(mddict[key])
            return mddict[key]
        else:
            return None

    def unrelativize(self, fil):
        '''make from a relative path into non-relative path'''
        return os.path.join(self.path, fil)

    def checkFileLevel(self, key, _fileid=None, shoulderror=True):
        '''getFileLevel, unrelativize, and make sure it exists'''
        val = self.getFileLevel(key, _fileid)
        if not val:
            return None
        pth = self.unrelativize(val)
        if os.path.exists(pth):
            return pth
        else:
            if shoulderror:
                error('%s does not exist' % pth)
            return None

    def setFileLevel( self, key, value, _fileid=None ):
        '''
        Set file-level metadata
        '''
        fileid = self.app.currentFID if _fileid==None else _fileid
        self.data[ 'files' ][ fileid ][ key ] = value
        self.write()

    def getCurrentFilename( self ):
        '''
        Helper function for interacting with traces
        '''
        return self.data[ 'files' ][ self.app.currentFID ][ 'name' ]

    def getCurrentTraceColor( self ):
        '''
        Returns color of the currently selected trace
        '''
        trace = self.app.Trace.getCurrentTraceName()
        if trace==None:
            return None
        return self.data[ 'traces' ][ trace ][ 'color' ]

    def setTraceColor( self, trace, color ):
        '''
        Set color for a particular trace name
        '''
        self.data[ 'traces' ][ trace ][ 'color' ] = color
        self.write()

    def getCurrentTraceAllFrames( self ):
        '''
        Returns a dictionary of with key->value give by frame->[crosshairs]
        for the current trace and file
        '''
        trace = self.app.Trace.getCurrentTraceName()
        filename = self.getCurrentFilename()
        try:
            return self.data[ 'traces' ][ trace ][ 'files' ][ filename ]
        except KeyError as e:
            return {}

    def getCurrentTraceTracedFrames(self):
        ''' '''
        frames = self.getCurrentTraceAllFrames()
        tracedFrames = []
        for frame,traces in frames.items():
            if traces != []:
                tracedFrames.append(frame)
        return tracedFrames

    def getTraceCurrentFrame( self, trace ):
        '''
        Returns a list of the crosshairs for the given trace at the current file
        and current frame
        '''
        filename = self.getCurrentFilename()
        frame    = str(self.app.frame)# if _frame==None else str(_frame)
        try:
            return self.data[ 'traces' ][ trace ][ 'files' ][ filename ][ frame ]
        except KeyError as e:
            return []

    def setCurrentTraceCurrentFrame( self, crosshairs ):
        '''
        Writes an array of the current crosshairs to the metadata dictionary at
        the current trace, current file, and current frame
        '''
        trace = self.app.Trace.getCurrentTraceName()
        filename = self.getCurrentFilename()
        frame = self.app.frame
        if trace not in self.data[ 'traces' ]:
            self.data[ 'traces' ][ trace ] = { 'files':{}, 'color':None }
        if filename not in self.data[ 'traces' ][ trace ][ 'files' ]:
            self.data[ 'traces' ][ trace ][ 'files' ][ filename ] = {}
        self.data[ 'traces' ][ trace ][ 'files' ][ filename ][ str(frame) ] = crosshairs
        self.write()

    def tracesExist( self, trace ):
        '''

        '''
        filename = self.getCurrentFilename()
        try:
            dict = self.data[ 'traces' ][ trace ][ 'files' ][ filename ]
            # debug(dict)
            return [x for x in dict if dict[x] != []]
        except KeyError as e:
            return []

    def reset(self, *args, **kwargs):
        raise NotImplementedError('cannot call MetadataModule::reset')

    def update(self, *args, **kwargs):
        raise NotImplementedError('cannot call MetadataModule::update')

    def grid(self, *args, **kwargs):
        raise NotImplementedError('cannot call MetadataModule::grid')

    def grid_remove(self, *args, **kwargs):
        raise NotImplementedError('cannot call MetadataModule::grid_remove')
