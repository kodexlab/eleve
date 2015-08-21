#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import glob
from distutils.core import setup, Extension

c_memory = Extension(
        name='eleve.c_memory.cmemory',
        sources=glob.glob('eleve/c_memory/*.cpp'),
        extra_compile_args=['--std=c++11'],
        libraries=['boost_python3', 'python3.4m'],
        include_dirs=['/usr/include/python3.4m'],
        undef_macros=['NDEBUG'], # I prefer to keep the assertions in the final code, just in case. Remove it if you want maximum perfs.
)

c_leveldb = Extension(
        name='eleve.c_leveldb.cleveldb',
        sources=glob.glob('eleve/c_leveldb/*.cpp'),
        extra_compile_args=['--std=c++11'],
        libraries=['boost_python3', 'python3.4m'],
        include_dirs=['/usr/include/python3.4m'],
        language='c++',
        undef_macros=['NDEBUG'], # I prefer to keep the assertions in the final code, just in case. (',) it if you want maximum perfs.
)

cwd = os.path.abspath(os.path.dirname(__file__))
readme = open(os.path.join(cwd, 'README.md')).read()

setup(
    name='eleve',
    version=0.1,
    description="Extraction de LExique par Variation d'Entropie - Lexicon extraction based on the variation of entropy",
    long_description=readme,
    author='Pierre Magistry',
    author_email='pierre@magistry.fr',
    url='http://kodexlab.com/eleve/',
    packages=['eleve'],
    classifiers=[
        "Programming Language :: Python",
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Natural Language :: French",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.2",
        "Topic :: Scientific/Engineering",
    ],
    ext_modules=[c_memory, c_leveldb],
)

