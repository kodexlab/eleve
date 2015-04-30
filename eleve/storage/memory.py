from __future__ import division
import math

from eleve.storage.base import Storage, DualStorage

class MemoryNode(object):
    """ Node used by :class:`MemoryTrie`
    """
    
    # to take a little less memory
    __slots__ = ['count', 'entropy_psum', 'childs']

    def __init__(self):
        self.count = 0
        self.entropy_psum = 0
        self.childs = {}

    @property
    def entropy(self):
        if self.count == 0:
            return None
        return math.log2(self.count) - self.entropy_psum / self.count

class MemoryTrie(Storage):
    """ Memory tree.
    """

    def __init__(self, depth):
        """
        :param depth: Maximum length of stored ngrams
        """
        self.depth = depth
        self.root = MemoryNode()

        # normalization params :
        # one for each level
        # on each level : count, mean, variance_psum (partial sum used to calculate the variance)
        self.normalization = [(0,0,0)] * depth

    def add_ngram(self, ngram, freq=1):
        """ Add a ngram to the tree.
        You can specify the number of times you add (or substract) that ngram by using the `freq` argument.
        """

        if len(ngram) != self.depth:
            raise ValueError("The size of the ngram parameter must be depth ({})".format(self.depth))

        if self.root.count + freq < 0:
            raise ValueError("Can't remove a non-existent ngram.")

        self._add_ngram(self.root, 0, ngram, freq)

    def _add_ngram(self, node, depth, ngram, freq):
        """ Recursive function used to add an ngram.
        """
        old_entropy = node.entropy

        node.count += freq
        try:
            token = ngram[0]
        except IndexError:
            return # ngram is empty (nothing left)

        # calculate entropy
        try:
            child = node.childs[token]
            node.entropy_psum -= child.count * math.log2(child.count)
        except KeyError:
            child = MemoryNode()
            node.childs[token] = child

        if child.count + freq < 0:
            raise ValueError("Can't remove a non-existent ngram.")

        try:
            old_ev = child.entropy - old_entropy
        except TypeError:
            # child.entropy is None: can't calculate EV
            old_ev = None

        # recurse, add the end of the ngram
        self._add_ngram(child, depth + 1, ngram[1:], freq)

        node.entropy_psum += child.count * math.log2(child.count or 1)

        # update normalization stats

        try:
            ev = child.entropy - node.entropy
        except TypeError:
            # child.entropy is None: can't calculate EV
            return

        count, mean, variance_psum = self.normalization[depth]

        old_mean = mean
        if old_ev is None: # first seen
            count += 1
            mean += (ev - mean) / count
            variance_psum += (ev - old_mean) * (ev - mean)
        else:
            mean += (ev - old_ev) / count
            variance_psum += (ev - old_mean) * (ev - mean) - (old_ev - old_mean) * (old_ev - mean)

        if old_entropy is not None:
            mean -= (node.entropy - old_entropy) * (len(node.childs) - 1) / count

        self.normalization[depth] = (count, mean, variance_psum)

    def query_node(self, ngram):
        """ Return a tuple with the main node data : (count, entropy).
        Count is the number of ngrams starting with the ``ngram`` parameter, entropy the entropy after the ngram.

        >>> m = MemoryTrie(3)
        >>> m.add_ngram(('le','petit','chat'))
        >>> m.add_ngram(('le','petit','chien'))
        >>> m.add_ngram(('le','gros','chien'))
        >>> m.query_node(('le', 'petit'))
        (2, 1.0)
        >>> m.query_node(None)[0] # None is for the root
        3
        >>> m.query_node(('le', 'petit')) == m.query_node(('le', 'gros'))
        False
        >>> m.add_ngram(('le','petit','chat'), -1)
        >>> m.query_node(('le', 'petit')) == m.query_node(('le', 'gros'))
        True
        """
        node = self.root
        while ngram:
            node = node.childs[ngram[0]]
            ngram = ngram[1:]
        return (node.count, node.entropy)

    def query_ev(self, ngram):
        """ Return the entropy variation for the ngram.
        """
        node = self.root
        last_node = node
        while ngram:
            last_node = node
            node = node.childs[ngram[0]]
            ngram = ngram[1:]

        return node.entropy - last_node.entropy

    def query_autonomy(self, ngram, spreadf = lambda x: 1):
        """ Return the autonomy (normalized entropy variation) for the ngram.
        """
        variance_count, mean, variance_psum = self.normalization[len(ngram) - 1]
        variance = math.sqrt(abs(variance_psum / variance_count))
        nev = (self.query_ev(ngram) - mean) / spreadf(variance)
        return nev


class MemoryStorage(DualStorage):
    """ Memory storage, that functions by adding ngrams and querying in both
    left-to-right and right-to-left order.
    It will do the mean of both result for each function.

    >>> m = MemoryStorage(3)
    >>> m.add_ngram(('le','petit','chat'))
    >>> m.add_ngram(('le','petit','chien'))
    >>> m.add_ngram(('pour','le','petit'), freq=2)
    >>> m.query_node(('le', 'petit'))
    (2.0, 0.5)
    """

    trie_class = MemoryTrie

if __name__ == '__main__':
    import doctest
    doctest.testmod()
