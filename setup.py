#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys
import glob
from distutils.core import setup, Extension

assert sys.version_info[0] >= 3, "For python >= 3 only"

def get_boost_lib():
    """     Try to find the appropriate option to pass to the linker, as it
    depends on the distribution. It's ugly, but it works...
    """
    major_minor = ''.join(map(str, sys.version_info[:2]))
    major = str(sys.version_info[0])

    libs = list(filter(lambda x: 'boost_python' in x, map(lambda x: x.split('/')[-1][3:].split('.')[0], glob.glob('/usr/lib/*') + glob.glob('/usr/lib/**/*'))))
    libs.sort()

    for l in libs:
        if major_minor in l:
            return l

    for l in libs:
        if major in l:
            return l

    assert len(libs) == 1, "You should have boost_python installed. We found these libs : %s" % libs
    return libs[0]

boost_python_lib = get_boost_lib()

c_memory = Extension(
        name='eleve.c_memory.cmemory',
        sources=glob.glob('eleve/c_memory/*.cpp'),
        extra_compile_args=['--std=c++11'],
        libraries=[boost_python_lib],
        undef_macros=['NDEBUG'], # I prefer to keep the assertions in the final code, just in case. Remove it if you want maximum perfs.
)

c_leveldb = Extension(
        name='eleve.c_leveldb.cleveldb',
        sources=glob.glob('eleve/c_leveldb/*.cpp'),
        extra_compile_args=['--std=c++11'],
        libraries=[boost_python_lib, 'leveldb'],
        language='c++',
        undef_macros=['NDEBUG'], # I prefer to keep the assertions in the final code, just in case. (',) it if you want maximum perfs.
)

cwd = os.path.abspath(os.path.dirname(__file__))
readme = open(os.path.join(cwd, 'README.rst')).read()

setup(
    name='eleve',
    version='0.1',
    description="Extraction de LExique par Variation d'Entropie - Lexicon extraction based on the variation of entropy",
    long_description=readme,
    author='KodexLab, Pierre Magistry, Korantin Auguste, Emmanuel Navarro',
    author_email='contact@kodexlab.com',
    url='https://github.com/kodexlab/eleve',
    packages=['eleve'],
    classifiers=[
        "Programming Language :: Python",
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Natural Language :: French",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Topic :: Scientific/Engineering",
    ],
    ext_modules=[c_memory, c_leveldb],
    install_requires=['plyvel'],
)

