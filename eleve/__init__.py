""":mod:`eleve`
================

"""
import warnings

__version__ = "20.10"

__all__ = [
    "MemoryStorage",
    "Segmenter",

]

from eleve.segment import Segmenter
from eleve.memory import MemoryStorage
from . import preprocessing as preprocessing
