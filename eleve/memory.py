from __future__ import division
import math
import operator
import logging
import pickle
import gzip

from eleve.storage import Storage

def entropy(counts):
    """ Calculate entropy from an iterator containing
    count of occurence for each value.

    >>> entropy([1,1])
    1.0
    >>> entropy([1])
    0.0
    >>> print('{:.4f}'.format(entropy([1,1,0,5,2])))
    1.6577
    """
    c, psum = 0, 0
    for i in counts:
        c += i
        psum += i * math.log2(i or 1)
    if c == 0:
        return 0
    return math.log2(c) - psum / c

def mean_stdev(values):
    """ Calculate mean and standard deviation from values of an iterator.

    >>> mean_stdev([1,3])
    (2.0, 1.0)
    >>> mean_stdev([2,2])
    (2.0, 0.0)
    """
    a, q, k = 0, 0, 0
    for v in values:
        k += 1
        old_a = a
        a += (v - a) / k
        q += (v - old_a)*(v - a)
    return (a, math.sqrt(q / k))

class MemoryNode(object):
    """ Node used by :class:`MemoryStorage`
    """
    
    # to take a little less memory
    __slots__ = ['count', 'entropy', 'childs', 'postings']

    def __init__(self):
        self.count = 0
        self.entropy = 0
        self.childs = {}
        self.postings = {}

class MemoryStorage(Storage):
    """ In-memory tree (made to be simple, no specific optimizations)
    """

    def __init__(self, depth, path=None):
        """
        :param depth: Maximum length of stored ngrams
        :param path: Path to the database (not used)
        """
        self.depth = depth
        self.root = MemoryNode()

        # normalization params :
        # one for each level
        # on each level : mean, stdev
        self.normalization = [(0,0)] * depth

        self.dirty = False

    @classmethod
    def load(cls, path):
        depth, root, normalization = pickle.load(gzip.GzipFile(path, 'rb'))
        s = cls(depth)
        s.root = root
        s.normalization = normalization
        return s

    def save(self, path):
        self.update_stats()
        o = (self.depth, self.root, self.normalization)
        with gzip.GzipFile(path, 'wb') as f:
            pickle.dump(o, f)

    def __iter__(self):
        """ Iterator on all the ngrams in the trie.
        Including partial ngrams (not leafs). So it gives a ngram for every node.
        """
        def _rec(ngram, node):
            for k, c in node.childs.items():
                yield ngram + [k]
                yield from _rec(ngram + [k], c)

        yield from _rec([], self.root)

    def update_stats(self):
        """ Update the internal statistics (like entropy, and stdev & means
        for the entropy variations. """
        if not self.dirty:
            return

        def update_entropy(node):
            node.entropy = entropy(map(operator.attrgetter('count'), node.childs.values()))
            for child in node.childs.values():
                update_entropy(child)

        update_entropy(self.root)

        def ve_for_depth(node, parent, depth):
            if depth == 0:
                yield node.entropy - parent.entropy
            else:
                for child in node.childs.values():
                    yield from ve_for_depth(child, node, depth - 1)

        for i in range(self.depth):
            self.normalization[i] = mean_stdev(ve_for_depth(self.root, None, i + 1))

        self.dirty = False

    def _check_dirty(self):
        if self.dirty:
            logging.warning("Updating the tree statistics (update_stats method), as we query it while dirty. This is a slow operation.")
            self.update_stats()

    def add_ngram(self, ngram, docid, freq=1):
        """ Add a ngram to the tree.
        You can specify the number of times you add (or substract) that ngram by using the `freq` argument.
        """

        if len(ngram) > self.depth:
            raise ValueError("The size of the ngram parameter must be less or equal than depth ({})".format(self.depth))

        if self.root.count + freq < 0:
            raise ValueError("Can't remove a non-existent ngram.")

        self._add_ngram(self.root, ngram, docid, freq)
        self.dirty = True

    def _add_ngram(self, node, ngram, docid, freq):
        """ Recursive function used to add a ngram.
        """

        node.count += freq
        try:
            token = ngram[0]
        except IndexError:
            try:
                node.postings[docid] += freq
            except KeyError:
                node.postings[docid] = freq
            return # ngram is empty (nothing left)

        try:
            child = node.childs[token]
        except KeyError:
            child = MemoryNode()
            node.childs[token] = child

        if child.count + freq < 0:
            raise ValueError("Can't remove a non-existent ngram.")

        # recurse, add the end of the ngram
        self._add_ngram(child, ngram[1:], docid, freq)

    def query_node(self, ngram):
        """ Return a tuple with the main node data : (count, entropy).
        Count is the number of ngrams starting with the ``ngram`` parameter, entropy the entropy after the ngram.
        """
        self._check_dirty()
        node = self.root
        while ngram:
            try:
                node = node.childs[ngram[0]]
            except KeyError:
                return (0, 0.)
            ngram = ngram[1:]
        return (node.count, node.entropy)

    def query_ev(self, ngram):
        """ Return the entropy variation for the ngram.
        """
        self._check_dirty()
        node = self.root
        last_node = node
        while ngram:
            last_node = node
            try:
                node = node.childs[ngram[0]]
            except KeyError:
                # FIXME: If both are zero, I should return NaN ?
                return -last_node.entropy if len(ngram) == 1 else 0.
            ngram = ngram[1:]

        return node.entropy - last_node.entropy

    def query_autonomy(self, ngram, z_score=True):
        """ Return the autonomy (normalized entropy variation) for the ngram.
        """
        self._check_dirty()
        mean, stdev = self.normalization[len(ngram) - 1]
        nev = self.query_ev(ngram) - mean
        if z_score:
            nev /= stdev
        return nev

if __name__ == '__main__':
    import doctest
    doctest.testmod()
