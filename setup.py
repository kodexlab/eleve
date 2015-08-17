#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from distutils.core import setup
from distutils.command.install import install

"""
class my_install(install):
    def run(self):
        install.run(self)

        os.chdir('eleve/c_memory')
        os.system('cmake . && make')
        os.chdir('../c_leveldb')
        os.system('cmake . && make')
"""

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
    #cmdclass={'install': my_install},
)

