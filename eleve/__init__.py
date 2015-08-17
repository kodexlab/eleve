__version__ = '1.0'
__all__ = ["MemoryStorage", "LeveldbStorage", "Segmenter",
           "CMemoryStorage", "PyMemoryStorage", "CLeveldbStorage", "PyLeveldbStorage"]

from segment import Segmenter

from memory_storage import MemoryStorage as PyMemoryStorage
from leveldb_storage import LeveldbStorage as PyLeveldbStorage

LeveldbStorage = PyLeveldbStorage

import warnings
try:
    from c_memory.cmemory import MemoryStorage as CMemoryStorage
except ImportError:
    warnings.warn("Unable to import the C++ memory backend. Eleve will be slower and consume more memory.")
    CMemoryStorage = None

MemoryStorage = CMemoryStorage or PyMemoryStorage

try:
    from c_leveldb.cleveldb import LeveldbStorage as CLeveldbStorage
except ImportError:
    warnings.warn("Unable to import the C++ leveldb backend. Eleve will be slower.")
    CLeveldbStorage = None

LeveldbStorage = CLeveldbStorage or PyLeveldbStorage
