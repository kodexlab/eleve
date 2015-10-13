""":mod:`eleve`
================

"""
import warnings

__all__ = ["MemoryStorage", "LeveldbStorage", "Segmenter",
           "CMemoryStorage", "PyMemoryStorage", "CLeveldbStorage", "PyLeveldbStorage"]

from eleve.segment import Segmenter

from eleve.memory import MemoryStorage as PyMemoryStorage
CMemoryStorage = None
try:
    from eleve.c_memory.cmemory import MemoryStorage as CMemoryStorage
except ImportError:
    warnings.warn("Unable to import the C++ memory backend. Eleve will be slower and consume more memory.")
MemoryStorage = CMemoryStorage or PyMemoryStorage

from eleve.leveldb import LeveldbStorage as PyLeveldbStorage
CLeveldbStorage = None
try:
    from eleve.c_leveldb.cleveldb import LeveldbStorage as CLeveldbStorage
except ImportError:
    warnings.warn("Unable to import the C++ leveldb backend. Eleve will be slower.")
LeveldbStorage = CLeveldbStorage or PyLeveldbStorage
