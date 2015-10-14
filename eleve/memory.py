""":mod:`eleve.memory`
======================

Provide full-python reference implementation of ``eleve`` storage and Trie.

"""
from __future__ import division
import math
import logging

__all__ = ["MemoryTrie", "MemoryStorage"]

def entropy(counts):
    """ Calculate entropy from an iterator containing
    count of occurence for each value.

    Each count must be greater or equal to 1. If it is
    not the case, it will be set to 1.

    >>> entropy([1,1])
    1.0
    >>> entropy([1])
    0.0
    >>> print('{:.4f}'.format(entropy([1,1,0,5,2])))
    1.6577
    """
    c, psum = 0, 0
    for i in counts:
        if i == 0:
            continue
        assert i >= 1
        c += i
        psum += i * math.log(i, 2)
    return (math.log(c, 2) - psum / c) if c > 0 else float('nan')

def mean_stdev(values):
    """ Calculate mean and standard deviation from values of an iterator.

    >>> mean_stdev([1,3])
    (2.0, 1.0)
    >>> mean_stdev([2,2])
    (2.0, 0.0)
    """
    a, q, k = 0, 0, 0
    for v in values:
        assert math.isfinite(v)
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

    def __init__(self, count=0):
        self.count = count
        self.entropy = float('nan')
        self.childs = {}


class MemoryLeaf(object):
    __slots__ = ['count']

    def __init__(self, count=0):
        self.count = count

    @property
    def entropy(self):
        return float('nan')


class MemoryTrie:
    """ In-memory tree (made to be simple, no specific optimizations)
    """

    def __init__(self, depth=10, terminals=['^', '$']):
        """ Constructor

        :param depth: Maximum length of stored ngrams
        :param terminals: Tokens that are in "terminals" array are counted as
        distinct in the entropy computation. By default, the symbols are for
        start and end of sentences.
        """
        self.depth = depth
        self.root = MemoryNode()
        # normalization params :
        # one for each level
        # on each level : mean, stdev
        self.normalization = [(0,0)] * depth
        self.terminals = set(terminals)
        self.dirty = False

    def clear(self):
        """ Clear the trie.
        """
        self.root = MemoryNode()
        self.dirty = True
        return self

    def iter_leafs(self):
        def _rec(ngram, node):
            if node.childs:
                for k, c in node.childs.items():
                    for i in _rec(ngram + [k], c): yield i
            elif node is not self.root:
                yield ngram

        for i in _rec([], self.root): yield i

    def _rec_update_entropy(self, node):
        """ Recursif update of entropy
        """
        counts = []
        for k, n in node.childs.items():
            if k in self.terminals:
                counts.extend(1 for _ in range(n.count))
            else:
                counts.append(n.count)
        node.entropy = entropy(counts)

        for child in node.childs.values():
            if isinstance(child, MemoryNode):
                self._rec_update_entropy(child)

    def _rec_ve_for_depth(self, node, parent, depth):
        """ Recursif generator of entropy variation (for a given level)
        """
        if depth == 0:
            if not math.isnan(node.entropy) and (node.entropy != 0 or parent.entropy != 0):
                yield node.entropy - parent.entropy
        elif isinstance(node, MemoryNode):
            for child in node.childs.values():
                for i in self._rec_ve_for_depth(child, node, depth - 1): yield i

    def update_stats(self):
        """ Update the internal statistics (like entropy, and stdev & means)
        for the entropy variations.

        Called automatically if the trie is modified and we then do queries on it.
        """
        if not self.dirty:
            return
        self._rec_update_entropy(self.root)
        for i in range(self.depth):
            try:
                self.normalization[i] = mean_stdev(self._rec_ve_for_depth(self.root, None, i + 1))
            except ZeroDivisionError:
                pass

        self.dirty = False

    def _check_dirty(self):
        if self.dirty:
            logging.warning("Updating the tree statistics (update_stats method), as we query it while dirty. This is a slow operation.")
            self.update_stats()

    def add_ngram(self, ngram, freq=1):
        """ Add a ngram to the trie.

        :param ngram: A list of tokens.
        :param freq: specify the number of times you add (or substract) that ngram.
        """
        if not 0 < len(ngram) <= self.depth:
            raise ValueError("The size of the ngram parameter must be in range(1, {} + 1)".format(self.depth))

        self.dirty = True

        node = self.root
        node.count += freq

        for i, token in enumerate(ngram):
            try:
                node = node.childs[token]
                node.count += freq
            except KeyError:
                child = MemoryLeaf(freq) if i == len(ngram) - 1 else MemoryNode(freq)
                assert isinstance(node, MemoryNode)
                node.childs[token] = child
                node = child

        assert isinstance(node, MemoryLeaf), str(ngram)

    def _lookup(self, ngram):
        """ Search for a node.

        :returns: a couple with the parent node and the node.
        :raises KeyError: if the node doesn't exists.
        """
        node = self.root
        last_node = node
        while ngram:
            last_node = node
            node = node.childs[ngram[0]]
            ngram = ngram[1:]
        return (last_node, node)

    def query_count(self, ngram):
        """ Query for the number of occurences we have seen the n-gram in the training data.

        :param ngram: A list of tokens.
        :returns: An integer.
        """
        try:
            _, node = self._lookup(ngram)
        except (KeyError, AttributeError):
            return 0.0
        return node.count

    def query_entropy(self, ngram):
        """ Query for the branching entropy.

        :param ngram: A list of tokens.
        :returns: A float, that can be NaN if it is not defined.
        """
        self._check_dirty()
        try:
            _, node = self._lookup(ngram)
        except (KeyError, AttributeError):
            return float('nan')
        return node.entropy
    
    def query_ev(self, ngram):
        """ Query for the branching entropy variation.

        :param ngram: A list of tokens.
        :returns: A float, that can be NaN if it is not defined.
        """
        self._check_dirty()

        if not ngram:
            return float('nan')

        try:
            last_node, node = self._lookup(ngram)
        except (KeyError, AttributeError):
            return float('nan')
        if not math.isnan(node.entropy) and (node.entropy != 0 or last_node.entropy != 0):
            return node.entropy - last_node.entropy
        return float('nan')

    def query_autonomy(self, ngram, z_score=True):
        """ Query the autonomy (normalized entropy variation) for the n-gram.

        :param ngram: A list of tokens.
        :param z_score: If True, compute the z_score ((value - mean) / stdev). If False, just substract the mean.
        :returns: A float, that can be NaN if it is not defined.
        """
        self._check_dirty()
        try:
            mean, stdev = self.normalization[len(ngram) - 1]
        except IndexError:
            return float('nan')
        ev = self.query_ev(ngram)
        if math.isnan(ev):
            return float('nan')
        nev = ev - mean
        if z_score:
            try:
                nev /= stdev
            except ZeroDivisionError:
                return float('nan')
        return nev


class MemoryStorage:
    """ Full-Python in-memory storage.
    """
    sentence_start = '^'
    sentence_end = '$'

    def __init__(self, ngram_length=5):
        """ Storage constructor.

        :param ngram_length: The maximum length of n-grams that can be stored.
        """
        assert isinstance(ngram_length, int) and ngram_length > 0
        self.ngram_length = ngram_length
        terminals = [self.sentence_start, self.sentence_end]
        self.bwd = MemoryTrie(self.ngram_length, terminals=terminals)
        self.fwd = MemoryTrie(self.ngram_length, terminals=terminals)

    def add_sentence(self, sentence, freq=1):
        """ Add a sentence to the model.

        :param sentence: The sentence to add. Should be a list of tokens.
        :param freq: The number of times to add this sentence. One by default. May be negative to "remove" a sentence.
        """
        if not sentence:
            return

        token_list = [self.sentence_start] + sentence + [self.sentence_start]
        for i in range(len(token_list) - 1):
            self.fwd.add_ngram(token_list[i:i+self.ngram_length], freq)
        token_list = token_list[::-1]
        for i in range(len(token_list) - 1):
            self.bwd.add_ngram(token_list[i:i+self.ngram_length], freq)

    def clear(self):
        """ Clear the training data in the model, effectively resetting it.
        """
        self.bwd.clear()
        self.fwd.clear()

    def update_stats(self):
        """ Update the entropies and normalization factors. This function is called automatically when you modify the model and then query it.
        """
        self.bwd.update_stats()
        self.fwd.update_stats()

    def query_autonomy(self, ngram):
        """ Query the autonomy for a ngram.

        :param ngram: A list of tokens.
        :returns: A float, that can be NaN if it is not defined.
        """
        result_fwd = self.fwd.query_autonomy(ngram)
        result_bwd = self.bwd.query_autonomy(ngram[::-1])
        if math.isnan(result_fwd) or math.isnan(result_bwd):
            return float('nan')
        return (result_fwd + result_bwd) / 2
     
    def query_ev(self, ngram):
        """ Query the entropy variation for a ngram.

        :param ngram: A list of tokens.
        :returns: A float, that can be NaN if it is not defined.
        """
        result_fwd = self.fwd.query_ev(ngram)
        result_bwd = self.bwd.query_ev(ngram[::-1])
        if math.isnan(result_fwd) or math.isnan(result_bwd):
            return float('nan')
        return (result_fwd + result_bwd) / 2

    def query_count(self, ngram):
        """ Query the count for a ngram (the number of time it appeared in the training corpus).

        :param ngram: A list of tokens.
        :returns: A float.
        """
        count_fwd = self.fwd.query_count(ngram)
        count_bwd = self.bwd.query_count(ngram[::-1])
        return (count_fwd + count_bwd) / 2

    def query_entropy(self, ngram):
        """ Query the branching entropy for a n-gram.

        :param ngram: A list of tokens.
        :returns: A float, that can be NaN if it is not defined.
        """
        entropy_fwd = self.fwd.query_entropy(ngram)
        entropy_bwd = self.bwd.query_entropy(ngram[::-1])
        if math.isnan(entropy_fwd) or math.isnan(entropy_bwd):
            return float('nan')
        return (entropy_fwd + entropy_bwd) / 2

