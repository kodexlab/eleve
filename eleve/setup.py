from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
from Cython.Build import cythonize

ext_modules =[Extension("DTrie",["DTrie.pyx"],language="c++")]

setup(
  name = 'Optimized stuffs for ELeVE',
  cmdclass = {'build_ext': build_ext},
  ext_modules = ext_modules
)

