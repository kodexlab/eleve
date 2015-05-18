from __future__ import division

import logging

from eleve.storage import Storage
from eleve.neo4j import Neo4jStorage
from eleve.memory import MemoryStorage

class MergeStorage(Storage):
    """ Storage implementation that put everything in a « hot » storage, that is fast.
    After a while, it will put the content of that « hot » storage in the « cold » storage,
    basically merging the tries.
    """

    hot_class = MemoryStorage
    max_hot_count = 100000

    cold_class = Neo4jStorage

    def __init__(self, depth, path=None):
        self.depth = depth

        self.hot_storage = self.hot_class(depth, path)
        self.cold_storage = self.cold_class(depth, path)

        self.hot_count = 0

    def clear(self):
        self.hot_storage.clear()
        self.cold_storage.clear()
        return self

    def _merge(self):
        logging.info("MergeStorage merging hot storage to cold one. Can take some time.")
        for ngram in self.hot_storage.iter_leafs():
            self.cold_storage.add_ngram(ngram, 1, self.hot_storage.query_node(ngram)[0])
            #FIXME: Add documents using postlists :
            #for docid, freq in self.hot_storage.query_postings(ngram):
            #    self.cold_storage.add_ngram(ngram, docid, freq)
        self.hot_storage.clear()

    def __iter__(self):
        self._merge()
        return iter(self.cold_storage)

    def update_stats(self):
        self._merge()
        return self.cold_storage.update_stats()

    def add_ngram(self, ngram, docid, freq=1):
        if self.hot_count > self.max_hot_count:
            self.hot_count = 0
            self._merge()
        else:
            self.hot_count += 1

        return self.hot_storage.add_ngram(ngram, docid, freq)

    def query_node(self, ngram):
        self._merge()
        return self.cold_storage.query_node(ngram)

    def query_ev(self, ngram):
        self._merge()
        return self.cold_storage.query_ev(ngram)

    def query_autonomy(self, ngram, z_score=True):
        self._merge()
        return self.cold_storage.query_autonomy(ngram, z_score)

    def query_postings(self, ngram):
        self._merge()
        return self.cold_storage.query_postings(ngram)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
