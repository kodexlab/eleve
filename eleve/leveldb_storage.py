import math

from eleve.memory_storage import MemoryStorage
from eleve.leveldb import LeveldbTrie

class LeveldbStorage(MemoryStorage):
    def __init__(self, order, path=None):
        """ Initialize the model.

        :param order: The maximum length of n-grams that can be stored.
        :param path: Path to the database where to load and store the model. If not specified, we use a temporary directory in /tmp (used for testing).
                     If the path is not existing an empty model will be created.
        """
        assert order > 0 and isinstance(order, int)
        self.order = order

        if path is None:
            path = '/tmp/leveldb_storage'

        self.bwd = LeveldbTrie(path=(path + '_bwd'))
        self.fwd = LeveldbTrie(path=(path + '_fwd'))
