from __future__ import division

from eleve.storage import Storage

class MergeStorage(Storage):
    """ Storage implementation that put everything in a « hot » storage, that is fast.
    After a while, it will put the content of that « hot » storage in the « cold » storage,
    basically merging the tries.
    """

    hot_class = None
    cold_class = None

    def __init__(self, depth, path=None):
        self.depth = depth

        self.hot_storage = self.hot_class(depth, path)
        self.cold_storage = self.cold_class(depth, path)

    def __iter__(self):
        raise NotImplementedError()

    def update_stats(self):
        raise NotImplementedError()

    def add_ngram(self, ngram, docid, freq=1):
        raise NotImplementedError()

    def query_node(self, ngram):
        raise NotImplementedError()

    def query_ev(self, ngram):
        raise NotImplementedError()

    def query_autonomy(self, ngram, z_score=True):
        raise NotImplementedError()

if __name__ == '__main__':
    import doctest
    doctest.testmod()
