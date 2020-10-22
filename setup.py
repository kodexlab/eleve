#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys
import glob
from setuptools import setup, Extension
from Cython.Build import cythonize
from Cython.Distutils import build_ext


assert sys.version_info[0] >= 3, "For python >= 3 only"

cwd = os.path.abspath(os.path.dirname(__file__))
readme = open(os.path.join(cwd, "README.rst")).read()

setup(
    name="eleve",
    version="20.10",
    description="Extraction de LExique par Variation d'Entropie - Lexicon extraction based on the variation of entropy",
    long_description=readme,
    author="Pierre Magistry, Korantin Auguste, Emmanuel Navarro",
    author_email="contact@kodexlab.com",
    url="https://github.com/kodexlab/eleve",
    packages=["eleve"],
    scripts=["scripts/eleve-train"],
    classifiers=[
        "Programming Language :: Python",
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Natural Language :: French",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Scientific/Engineering",
    ],
    ext_modules=cythonize(["eleve/cython_storage.pyx"],
                          compiler_directives={'language_level' : "3"},
                          annotate=True),
    install_requires=["plyvel"],
)
