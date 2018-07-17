from libc.math cimport (log10)
from cython.parallel import prange
from cython.view cimport array as cvarray
cimport numpy as np
import numpy as np

#cdef float x, max_freq_bin
#cdef list stft_spectra

# cpdef double[:,:] stft2level(np.ndarray[np.float32_t, ndim=2] stft_spectra, float max_freq_bin):
#   cdef int x = len(stft_spectra)
#   cdef int y = len(stft_spectra[0])
#   #cdef list magnitude_spectra = [ abs(x) for x in stft_spectra ]
#   #cdef double[:, :] magnitude_spectra = np.absolute(stft_spectra)
#   #magnitude_spectra = cvarray(shape=(x, y), itemsize=sizeof(double), format="d")
#   cdef np.ndarray[double, ndim=2, mode = 'c'] magnitude_spectra = np.ascontiguousarray(np.absolute(stft_spectra), dtype = double)
#   magnitude_spectra = np.absolute(stft_spectra)
#   #tmp_magnitude_spectra = [ abs(x) for x in stft_spectra ]
#   #cdef double[:, :] magnitude_spectra = tmp_magnitude_spectra
#   #max_magnitude = max([ max(x) for x in magnitude_spectra ])
#   max_magnitude = np.max(magnitude_spectra)
#   cdef float min_magnitude = max_magnitude / 1000.0
#   cdef int t, k
#   #cdef list level_spectra = []
#   #cdef double[:, :] level_spectra[x][y]
#   #cdef double[:, :] level_spectra = np.zeros((x,y))
#   level_spectra = cvarray(shape=(x, y), itemsize=sizeof(double), format="d")
#   type(level_spectra)
#   for t in prange(0,len(magnitude_spectra), nogil=True):
#   #for t in range(0,len(magnitude_spectra)):
#     #level_spectra.append([])
#     #for k in prange(0,len(magnitude_spectra[t]), nogil=True):
#     for k in range(0,len(magnitude_spectra[t])):
#       #magnitude_spectra[t][k] /= min_magnitude
#       magnitude_spectra[t][k] = magnitude_spectra[t][k] / min_magnitude
#       if magnitude_spectra[t][k] < 1:
#         magnitude_spectra[t][k] = 1
#       if k < max_freq_bin:
#         level_spectra[t][k] = 20*log10(magnitude_spectra[t][k])
#   return(level_spectra)

cpdef double[:,:] stft2level(np.ndarray[np.float64_t, ndim=2] stft_spectra, int max_freq_bin):
    cdef np.ndarray[np.float64_t, ndim=2] magnitude_spectra = np.absolute(stft_spectra)
    cdef float max_magnitude = np.max(magnitude_spectra)
    cdef float min_magnitude = max_magnitude / 1000.0
    #print("fast", np.shape(stft_spectra), min_magnitude, max_magnitude, np.shape(magnitude_spectra))
    cdef int x = len(stft_spectra)
    cdef int y = len(stft_spectra[0])
    #cdef np.ndarray[np.float64_t, ndim=2] level_spectra = cvarray(shape=(x, y), itemsize=sizeof(double), format="d")
    cdef np.ndarray[np.float64_t, ndim=2] level_spectra = np.zeros((x,max_freq_bin))
    #for t in prange(len(magnitude_spectra), nogil=True):
    for t in range(len(magnitude_spectra)):
        for k in range(len(magnitude_spectra[t])):
            magnitude_spectra[t, k] = magnitude_spectra[t, k] / min_magnitude
            if magnitude_spectra[t, k] < 1:
                magnitude_spectra[t, k] = 1
            if k < max_freq_bin:
                #print(t, k)
                level_spectra[t, k] = 20*log10(magnitude_spectra[t, k])
    #print("fast", np.shape(level_spectra))
    return(level_spectra)
