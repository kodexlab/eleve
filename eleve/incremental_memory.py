from __future__ import division
import math
import pickle
import gzip

from eleve.storage import Storage

class IncrementalMemoryNode(object):
    """ Node used by :class:`IncrementalMemoryTrie`
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
        if self.entropy_psum == 0 and not self.childs:
            return 0.
        return math.log2(self.count) - self.entropy_psum / self.count

class IncrementalMemoryStorage(Storage):
    """ IncrementalMemory tree.
    """

    def __init__(self, depth):
        """
        :param depth: Maximum length of stored ngrams
        """
        self.depth = depth
        self.root = IncrementalMemoryNode()

        # normalization params :
        # one for each level
        # on each level : count, mean, variance
        self.normalization = [(0,0,0)] * depth
    
    @classmethod
    def load(cls, path):
        depth, root, normalization = pickle.load(gzip.GzipFile(path, 'rb'))
        s = cls(depth)
        s.root = root
        s.normalization = normalization
        return s

    def save(self, path):
        o = (self.depth, self.root, self.normalization)
        with gzip.GzipFile(path, 'wb') as f:
            pickle.dump(o, f)

    def add_ngram(self, ngram, freq=1):
        """ Add a ngram to the tree.
        You can specify the number of times you add (or substract) that ngram by using the `freq` argument.
        """

        if len(ngram) > self.depth:
            raise ValueError("The size of the ngram parameter must be less than depth ({})".format(self.depth))

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
        except IndexError: # ngram is empty (nothing left)
            # that assert is an important point : the count of the node should
            # be equal to the sum of the count of its child. If it is not, our
            # incremental entropy calculation is flawed.
            assert not node.childs, "Can't add a \"partial\" ngram in an incremental tree."
            return

        # calculate entropy
        try:
            child = node.childs[token]
            node.entropy_psum -= child.count * math.log2(child.count)
        except KeyError:
            child = IncrementalMemoryNode()
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

        count, mean, variance = self.normalization[depth]

        if old_ev is None: # first seen
            count += 1
            mean += (ev - mean) / count
        else:
            mean += (ev - old_ev) / count

        if old_entropy is not None:
            mean -= (node.entropy - old_entropy) * (len(node.childs) - 1) / count

        self.normalization[depth] = (count, mean, variance)

    def query_node(self, ngram):
        """ Return a tuple with the main node data : (count, entropy).
        Count is the number of ngrams starting with the ``ngram`` parameter, entropy the entropy after the ngram.

        >>> m = IncrementalMemoryStorage(3)
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
            try:
                node = node.childs[ngram[0]]
            except KeyError:
                # FIXME: If both are zero, I should return NaN ?
                return (0, 0.)
            ngram = ngram[1:]
        return (node.count, node.entropy)

    def query_ev(self, ngram):
        """ Return the entropy variation for the ngram.
        """
        node = self.root
        last_node = node
        while ngram:
            last_node = node
            try:
                node = node.childs[ngram[0]]
            except KeyError:
                return -last_node.entropy
            ngram = ngram[1:]

        return node.entropy - last_node.entropy

    def query_autonomy(self, ngram, z_score=True):
        """ Return the autonomy (normalized entropy variation) for the ngram.
        """
        _, mean, variance = self.normalization[len(ngram) - 1]

        assert not z_score, \
            "Can't use z-score. Incremental variance not implemented."

        nev = self.query_ev(ngram) - mean
        if z_score:
            nev /= variance
        return nev

if __name__ == '__main__':
    import doctest
    doctest.testmod()
