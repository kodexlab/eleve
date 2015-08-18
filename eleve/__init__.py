__all__ = ["MemoryStorage", "LeveldbStorage", "Segmenter",
           "CMemoryStorage", "PyMemoryStorage", "CLeveldbStorage", "PyLeveldbStorage"]

from eleve.segment import Segmenter

from eleve.memory_storage import MemoryStorage as PyMemoryStorage
from eleve.leveldb_storage import LeveldbStorage as PyLeveldbStorage

LeveldbStorage = PyLeveldbStorage

import warnings
try:
    from eleve.c_memory.cmemory import MemoryStorage as CMemoryStorage
except ImportError:
    warnings.warn("Unable to import the C++ memory backend. Eleve will be slower and consume more memory.")
    CMemoryStorage = None

MemoryStorage = CMemoryStorage or PyMemoryStorage

try:
    from eleve.c_leveldb.cleveldb import LeveldbStorage as CLeveldbStorage
except ImportError:
    warnings.warn("Unable to import the C++ leveldb backend. Eleve will be slower.")
    CLeveldbStorage = None

LeveldbStorage = CLeveldbStorage or PyLeveldbStorage
