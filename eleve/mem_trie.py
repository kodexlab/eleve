from __future__ import division
from trie_storage import TrieStorage
from storage import Storage
import pickle
import collections
import math

class MemNode(object):
    def __init__(self):
        self.count = 0
        self.entropy_psum = 0
        self.childs = {}

    @property
    def entropy(self):
        if self.count == 0:
            return None
        return math.log2(self.count) - self.entropy_psum / self.count

class MemTrie(Storage):
    """
    Memory tree.

    >>> m = MemTrie(None, 3)
    >>> m.add_ngram((0,1,2))
    >>> m.add_ngram((0,1,3))
    >>> m.query_nev((0,1))
    """

    def __init__(self, path, depth):
        assert path is None

        self.normalization = [(0,0,0)]*depth
        self.depth = depth

        self.root = MemNode()

        #with open(path, 'rb') as f:
        #    self.root = pickle.load(f)

    def add_ngram(self, ngram):
        assert len(ngram) <= self.depth
        self._add_ngram(self.root, [], ngram)

    def _add_ngram(self, node, parents, ngram):
        old_entropy = node.entropy

        node.count += 1
        try:
            token = ngram[0]
        except IndexError:
            return # ngram is empty (nothing left)

        # calculate entropy

        try:
            child = node.childs[token]
            node.entropy_psum -= child.count * math.log2(child.count)
        except KeyError:
            child = MemNode()
            node.childs[token] = child

        node.entropy_psum += (child.count + 1) * math.log2(child.count + 1)

        # recurse

        self._add_ngram(child, parents + [node], ngram[1:])

        depth = len(parents)
        if depth == 0:
            return

        # update normalization stats
        
        ve = node.entropy - parents[-1].entropy
        count, mean, variance_psum = self.normalization[depth - 1]

        old_mean = mean
        if node.count == 1: # first seen
            count += 1
            mean += (ve - mean) / count
            variance_psum += (ve - old_mean) * (ve - mean)
        else:
            mean += (ve - old_entropy) / count
            variance_psum += (ve - old_mean) * (ve - mean) - (old_entropy - old_mean) * (old_entropy - mean)

        self.normalization[depth - 1] = (count, mean, variance_psum)

    def query_ev(self, ngram):
        node = self.root
        last_node = node
        while ngram:
            last_node = node
            node = node.childs[ngram[0]]
            ngram = ngram[1:]

        return node.entropy - last_node.entropy

    def query_autonomy(self, ngram, spreadf = lambda x: 1.):
        variance_count, mean, variance_psum = self.normalization[len(ngram) - 1]
        variance = math.sqrt(variance_psum / variance_count)
        nev = (self.query_ev(ngram) - mean) / spreadf(variance)
        return nev

class MemStorage(TrieStorage):
    trie_class = MemTrie

if __name__ == '__main__':
    import doctest
    doctest.testmod()
