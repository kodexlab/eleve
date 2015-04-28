#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from setuptools import setup, find_packages
from eleve import __version__
from distutils.core import setup
from distutils.extension import Extension

#from Cython.Distutils import build_ext
#from Cython.Build import cythonize


cwd = os.path.abspath(os.path.dirname(__file__))
readme = open(os.path.join(cwd, 'README.md')).read()

setup(
    name='eleve',
    version=__version__,
    description="Extraction de LExique par Variation d'Entropie - Lexicon extraction based on the variation of entropy",
    long_description=readme,
    author='Pierre Magistry',
    author_email='pierre@magistry.fr',
    url='http://kodexlab.com/eleve/',
#    install_requires=['reliure','cython'],
#    ext_modules=cythonize(['eleve/DTrie.pyx']),
    packages=['eleve'] + ['eleve.%s' % submod for submod in find_packages('eleve')],
    classifiers=[
        "Programming Language :: Python",
#        "Programming Language :: Cython", 
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Natural Language :: French",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
        "Topic :: Scientific/Engineering",
    ],
)

