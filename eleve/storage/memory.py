from __future__ import division
import math
import operator

from eleve.storage.base import Storage, DualStorage

def entropy(counts):
    """ Calculate entropy from a list of counts.
    >>> entropy([1,1])
    1.0
    >>> entropy([1])
    0.0
    >>> print('{:.4f}'.format(entropy([1,1,0,5,2])))
    1.6577
    """
    c = 0
    psum = 0
    for i in counts:
        c += i
        psum += i * math.log2(i or 1)
    if c == 0:
        return 0
    return math.log2(c) - psum / c

def mean_variance(values):
    """ Calculate mean and variance from values of an iterator
    >>> mean_variance([1,3])
    (2.0, 1.0)
    >>> mean_variance([2,2])
    (2.0, 0.0)
    """
    a = 0
    q = 0
    k = 0
    for v in values:
        k += 1
        old_a = a
        a += (v - a) / k
        q += (v - old_a)*(v - a)
    return (a, math.sqrt(q / k))

class MemoryNode(object):
    """ Node used by :class:`MemoryTrie`
    """
    
    # to take a little less memory
    __slots__ = ['count', 'entropy', 'childs']

    def __init__(self):
        self.count = 0
        self.entropy = 0
        self.childs = {}

class MemoryTrie(Storage):
    """ In-memory tree (made to be simple, no specific optimizations)
    """

    def __init__(self, depth):
        """
        :param depth: Maximum length of stored ngrams
        """
        self.depth = depth
        self.root = MemoryNode()

        # normalization params :
        # one for each level
        # on each level : mean, variance
        self.normalization = [(0,0)] * depth

        self.dirty = False

    def __iter__(self):
        def _rec(ngram, node):
            for k, c in node.childs.items():
                yield ngram + [k]
                yield from _rec(ngram + [k], c)

        yield from _rec([], self.root)

    def update_stats(self):
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
            self.normalization[i] = mean_variance(ve_for_depth(self.root, None, i + 1))

        self.dirty = False

    def check_dirty(self):
        if self.dirty:
            raise RuntimeError("You must update the tree stats before doing a query.")

    def add_ngram(self, ngram, freq=1):
        """ Add a ngram to the tree.
        You can specify the number of times you add (or substract) that ngram by using the `freq` argument.
        """

        if not 1 <= len(ngram) <= self.depth:
            raise ValueError("The size of the ngram parameter must be depth ({})".format(self.depth))

        if self.root.count + freq < 0:
            raise ValueError("Can't remove a non-existent ngram.")

        self._add_ngram(self.root, ngram, freq)
        self.dirty = True

    def _add_ngram(self, node, ngram, freq):
        """ Recursive function used to add a ngram.
        """

        node.count += freq
        try:
            token = ngram[0]
        except IndexError:
            return # ngram is empty (nothing left)

        try:
            child = node.childs[token]
        except KeyError:
            child = MemoryNode()
            node.childs[token] = child

        if child.count + freq < 0:
            raise ValueError("Can't remove a non-existent ngram.")

        # recurse, add the end of the ngram
        self._add_ngram(child, ngram[1:], freq)

    def query_node(self, ngram):
        """ Return a tuple with the main node data : (count, entropy).
        Count is the number of ngrams starting with the ``ngram`` parameter, entropy the entropy after the ngram.
        """
        self.check_dirty()
        node = self.root
        while ngram:
            # FIXME: KeyError ?
            node = node.childs[ngram[0]]
            ngram = ngram[1:]
        return (node.count, node.entropy)

    def query_ev(self, ngram):
        """ Return the entropy variation for the ngram.
        """
        self.check_dirty()
        node = self.root
        last_node = node
        while ngram:
            last_node = node
            # FIXME: KeyError ?
            node = node.childs[ngram[0]]
            ngram = ngram[1:]

        return node.entropy - last_node.entropy

    def query_autonomy(self, ngram, spreadf = lambda x: 1):
        """ Return the autonomy (normalized entropy variation) for the ngram.
        """
        self.check_dirty()
        mean, variance = self.normalization[len(ngram) - 1]
        nev = (self.query_ev(ngram) - mean) / spreadf(variance)
        return nev


class MemoryStorage(DualStorage):
    """ Memory storage, that functions by adding ngrams and querying in both
    left-to-right and right-to-left order.
    It will do the mean of both result for each function.
    """

    trie_class = MemoryTrie

if __name__ == '__main__':
    import doctest
    doctest.testmod()
