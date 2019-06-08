""":mod:`eleve`
================

"""
import warnings

__version__ = "15.10"

__all__ = [
    "MemoryStorage",
    "LeveldbStorage",
    "Segmenter",
    "CMemoryStorage",
    "PyMemoryStorage",
    "CLeveldbStorage",
    "PyLeveldbStorage",
]

from eleve.segment import Segmenter

from eleve.memory import MemoryStorage as PyMemoryStorage

CMemoryStorage = None
try:
    from eleve.c_memory.cmemory import MemoryStorage as CMemoryStorage
except ImportError as e:
    warnings.warn(
        "Unable to import the C++ memory backend. Eleve will be slower and consume more memory. Error: %s"
        % e
    )
MemoryStorage = CMemoryStorage or PyMemoryStorage

from eleve.leveldb import LeveldbStorage as PyLeveldbStorage

CLeveldbStorage = None
try:
    from eleve.c_leveldb.cleveldb import LeveldbStorage as CLeveldbStorage
except ImportError as e:
    warnings.warn(
        "Unable to import the C++ leveldb backend. Eleve will be slower. Error: %s" % e
    )
LeveldbStorage = CLeveldbStorage or PyLeveldbStorage
