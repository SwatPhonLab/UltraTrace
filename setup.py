from distutils.core import setup
from Cython.Build import cythonize
from distutils.extension import Extension
from Cython.Distutils import build_ext
import os, numpy

os.environ["CC"] = "g++-8"
os.environ["CXX"] = "g++-8"

ext_modules=[
    Extension("stft2level",
        ["stft2level.pyx"],
        libraries=["m"],
        extra_compile_args = ["-O3", "-ffast-math", "-march=native", "-fopenmp" ],
        extra_link_args=['-fopenmp'],
        include_dirs=[numpy.get_include()]
    )
]

setup(
  name = "stft2level",
  cmdclass = {"build_ext": build_ext},
  ext_modules = ext_modules
)
