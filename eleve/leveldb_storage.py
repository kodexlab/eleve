import math

from eleve.memory_storage import MemoryStorage

class LeveldbStorage(MemoryStorage):
    def __init__(self, order, path=None):
        assert order > 0 and isinstance(order, int)
        self.order = order

        if path is None:
            path = '/tmp/leveldb_storage'

        self.bwd = LeveldbTrie(path=(path + '_bwd'))
        self.fwd = LeveldbTrie(path=(path + '_fwd'))
