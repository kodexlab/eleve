""":mod:`eleve.memory`
======================

Provide full-python reference implementation of ``eleve`` storage and Trie.

"""
from __future__ import division
import math
import logging

import pickle

__all__ = ["MemoryTrie", "MemoryStorage"]

NaN = float("nan")


def extract_ngrams(token_list, ngram_length):
    for i in range(len(token_list) - 1):
        yield token_list[i : i + ngram_length]


class MemoryNode(object):
    """ Node used by :class:`MemoryTrie`
    """

    # to take a little less memory
    __slots__ = ["count", "entropy", "childs"]

    def __init__(self, count=0):
        self.count = count
        self.entropy = float("nan")
        self.childs = {}

    def update_entropy(self, terminals):
        """ Update the entropy of the node.

        :param terminals: a set of bytes. If a token is inside that set, it will
         count as N different tokens instead of a token with count N.
        """
        entropy = 0
        sum_counts = 0
        for token, child in self.childs.items():
            if child.count == 0:
                continue
            sum_counts += child.count
            if token in terminals:
                entropy += (child.count / self.count) * math.log(self.count, 2)
            else:
                entropy -= (child.count / self.count) * math.log(
                    child.count / self.count, 2
                )
        if not sum_counts:
            entropy = NaN
        else:
            assert sum_counts == self.count
        if self.entropy != entropy and not (
            math.isnan(self.entropy) and math.isnan(entropy)
        ):
            self.entropy = entropy

    def iter_childs(self):
        """ Returns an iterator over childs nodes
        """
        return self.childs.values()


class MemoryLeaf(object):
    __slots__ = ["count"]

    def __init__(self, count=0):
        self.count = count

    @property
    def entropy(self):
        return float("nan")

    def to_node(self):
        return MemoryNode(count=self.count)


class MemoryTrie:
    """ In-memory tree (made to be simple, no specific optimizations)
    """

    def __init__(self, terminals=frozenset()):
        """ Constructor

        :param terminals: Tokens that are in "terminals" array are counted as
          distinct in the entropy computation. By default, the symbols are for
          start and end of sentences.
        """
        self.root = MemoryNode()
        # normalization params :
        #   * one for each level
        #   * on each level : mean, stdev
        #   * WARNING: self.normalization[0] gives data for depth 1 (depth 0 is root and always NaN, NaN)
        self.normalization = []
        self.terminals = frozenset(terminals)
        self.dirty = True

    def max_depth(self):
        """ Returns the maximum depth of the Trie

        >>> trie = MemoryTrie()
        >>> trie.max_depth()
        0
        >>> trie.add_ngram(["A", "B", "C"])
        >>> trie.max_depth()
        3
        """
        self._check_dirty()
        return len(self.normalization)

    def clear(self):
        """ Clear the trie.
        """
        self.root = MemoryNode()
        self.dirty = True
        return self

    def iter_leafs(self):
        def _rec(ngram, node):
            if node.childs:
                for token, child in node.childs.items():
                    for i in _rec(ngram + [token], child):
                        yield i
            elif node is not self.root:
                yield ngram

        for i in _rec([], self.root):
            yield i


    def prune(self, minus=1):
        """"Recursively remove <minus> occurrence of all ngrams
        """
        self.dirty = True
        def rec(node):
            n = 0
            if hasattr(node, "childs"):
                for _, child in node.childs.items():
                    n += rec(child)
                node.childs = {tok: c for tok, c in node.childs.items() if c.count > 0}
                node.count -= n
            else:
                n = min(minus, node.count)
                node.count -= minus
            return n
        n = rec(self.root)
        print(n)
        #self.root.count -= n


    def _update_stats_rec(self, parent_entropy, depth, node):
        """ Recurively update both entropy and normalization vector
        """
        # extend normalization vector if needed
        while len(self.normalization) < depth:
            self.normalization.append((0.0, 0.0, 0))
        # if MemoryLeaf nothing else should be done
        if isinstance(node, MemoryLeaf):
            return
        node.update_entropy(self.terminals)
        # update entropy variation mean and std if possible (not NaN)
        if (
            depth > 0
            and not math.isnan(node.entropy)
            and (node.entropy or parent_entropy)
        ):
            ev = node.entropy - parent_entropy
            mean, stdev, count = self.normalization[depth - 1]
            old_mean = mean
            count += 1
            mean += (ev - old_mean) / count
            stdev += (ev - old_mean) * (ev - mean)
            self.normalization[depth - 1] = mean, stdev, count
        # recurifs calls
        for child in node.iter_childs():
            self._update_stats_rec(node.entropy, depth + 1, child)

    def update_stats(self):
        """ Update the internal statistics (like entropy, and stdev & means)
        for the entropy variations.

        Called automatically if the trie is modified and we then do queries on it.
        """
        if not self.dirty:
            return
        self.normalization = []
        self._update_stats_rec(NaN, 0, self.root)
        for pseudo_depth, (mean, _stdev, count) in enumerate(self.normalization):
            stdev = math.sqrt(_stdev / (count or 1))
            self.normalization[pseudo_depth] = (mean, stdev)
        self.dirty = False

    def _check_dirty(self):
        if self.dirty:
            logging.warning(
                "Updating the tree statistics (update_stats method), as we query it while dirty. This is a slow operation."
            )
            self.update_stats()

    def add_ngram(self, ngram, freq=1):
        """ Add a ngram to the trie.

        :param ngram: A list of tokens.
        :param freq: specify the number of times you add (or substract) that ngram.
        """
        if freq <= 0:
            raise ValueError("freq should be larger or equal to 1")
        if len(ngram) == 0:
            logging.warning("Adding empty ngram just do nothing.")
            return
        self.dirty = True
        parent = self.root
        parent.count += freq
        for depth, token in enumerate(ngram):
            try:
                child = parent.childs[token]
                child.count += freq
                # transform leaf to node, if we are not at the end
                if depth < len(ngram) - 1 and isinstance(child, MemoryLeaf):
                    child = child.to_node()
                    parent.childs[token] = child
            except KeyError:  # node do not exist yet
                child = MemoryNode(freq) if depth < len(ngram) - 1 else MemoryLeaf(freq)
                parent.childs[token] = child
            parent = child

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
            return float("nan")
        return node.entropy

    def query_ev(self, ngram):
        """ Query for the branching entropy variation.

        :param ngram: A list of tokens.
        :returns: A float, that can be NaN if it is not defined.
        """
        self._check_dirty()
        if not ngram:
            return float("nan")
        try:
            last_node, node = self._lookup(ngram)
        except (KeyError, AttributeError):
            return float("nan")
        if not math.isnan(node.entropy) and (
            node.entropy != 0 or last_node.entropy != 0
        ):
            return node.entropy - last_node.entropy
        return float("nan")

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
            return float("nan")
        ev = self.query_ev(ngram)
        if math.isnan(ev):
            return float("nan")
        nev = ev - mean
        if z_score:
            try:
                nev /= stdev
            except ZeroDivisionError:
                return float("nan")
        return nev

from .cython_storage import CythonTrie

class MemoryStorage:
    """ Full-Python in-memory storage.
    """

    # Use PRIVATE_USE_AREA codes
    sentence_start = "\ue02b"  # in utf8 : b"\xee\x80\xab"
    #  see http://www.fileformat.info/info/unicode/char/e02b/index.htm
    sentence_end = "\ue02d"  # in utf8 : b"\xee\x80\xad"
    #  see http://www.fileformat.info/info/unicode/char/e02d/index.htm

    def __init__(self, default_ngram_length=5):
        """ Storage constructor.

        :param default_ngram_length: the default maximum length of n-gram beeing
          stored. May be overriden in :func:`add_sentence`.
        """
        assert isinstance(default_ngram_length, int) and default_ngram_length > 0
        self._default_ngram_length = default_ngram_length
        terminals = frozenset([self.sentence_start, self.sentence_end])
        self.bwd = CythonTrie(terminals=terminals) # MemoryTrie(terminals=terminals)
        self.fwd = CythonTrie(terminals=terminals) # MemoryTrie(terminals=terminals)
        #self.bwd = MemoryTrie(terminals=terminals)
        #self.fwd = MemoryTrie(terminals=terminals)

    def get_voc(self):
        return self.fwd.get_voc()

    @property
    def default_ngram_length(self):
        return self._default_ngram_length

    def add_sentence(self, sentence, freq=1, ngram_length=None):
        """ Add a sentence to the model.

        :param sentence: The sentence to add. Should be a list of tokens.
        :param freq: The number of times to add this sentence. One by default. May be negative to "remove" a sentence.
        :param ngram_length: The length of n-grams that are stored. If None the
          default value setup in __init__ is used.
        """
        if freq <= 0:
            raise ValueError("freq should be larger or equal to 1")
        if not sentence:
            return
        if ngram_length is None:
            ngram_length = self.default_ngram_length
        # We add sentence_start and sentence_end at both ends. We cast it to the type of sentence, so it
        # works whether sentence is a str, tuple, or list.
        token_list = type(sentence)(self.sentence_start) + sentence + type(sentence)(self.sentence_end)
        for ngram in extract_ngrams(token_list, ngram_length):
            self.fwd.add_ngram(ngram, freq)
        for ngram in extract_ngrams(token_list[::-1], ngram_length):
            self.bwd.add_ngram(ngram, freq)

    def clear(self):
        """ Clear the training data in the model, effectively resetting it.
        """
        self.bwd.clear()
        self.fwd.clear()

    def prune(self, minus=1):
        self.bwd.prune(minus)
        self.fwd.prune(minus)

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
        # Notice that the above can be NaN. In which case it's propagated anyway.
        return (result_fwd + result_bwd) / 2

    def query_ev(self, ngram):
        """ Query the entropy variation for a ngram.

        :param ngram: A list of tokens.
        :returns: A float, that can be NaN if it is not defined.
        """
        result_fwd = self.fwd.query_ev(ngram)
        result_bwd = self.bwd.query_ev(ngram[::-1])
        # Notice that the above can be NaN. In which case it's propagated anyway.
        return (result_fwd + result_bwd) / 2

    def query_count(self, ngram):
        """ Query the count for a ngram (the number of time it appeared in the training corpus).

        :param ngram: A list of tokens.
        :returns: A float.
        """
        return self.fwd.query_count(ngram)

    def query_entropy(self, ngram):
        """ Query the branching entropy for a n-gram.

        :param ngram: A list of tokens.
        :returns: A float, that can be NaN if it is not defined.
        """
        entropy_fwd = self.fwd.query_entropy(ngram)
        entropy_bwd = self.bwd.query_entropy(ngram[::-1])
        # Notice that the above can be NaN. In which case it's propagated anyway.
        return (entropy_fwd + entropy_bwd) / 2


class CSVStorage:
    """
    This is a non-trainable storage.
    It relies on a CSV dump from a MemoryStorage and can only be used to
    perform segmentation and autonomy query
    """
    # Use PRIVATE_USE_AREA codes
    sentence_start = "\ue02b"  # in utf8 : b"\xee\x80\xab"
    #  see http://www.fileformat.info/info/unicode/char/e02b/index.htm
    sentence_end = "\ue02d"  # in utf8 : b"\xee\x80\xad"

    #  see http://www.fileformat.info/info/unicode/char/e02d/index.htm

    def __init__(self, path, delim=""):
        self.data = {}
        self.delim = delim
        lmax = 0
        with open(path) as f:
            for line in f:
                fields = line.strip().split("\t")
                ng = tuple(fields[0]) if delim == '' else tuple(fields[0].split(delim))
                self.data[ng] = (float(fields[1]), int(fields[2]))
                if len(ng) > lmax:
                    lmax = len(fields[0])
        self._ngram_length = lmax + 1
        print(lmax)

    def query_autonomy(self, ngram):
        try:
            return self.data[tuple(ngram)][0]
        except:
            return float("nan")

    def query_count(self, ngram):
        try:
            return self.data[tuple(ngram)][1]
        except:
            return 0

    @property
    def default_ngram_length(self):
        return self._ngram_length

    @staticmethod
    def writeCSV(storage,voc,  path, delim=''):
        with open(path, "w") as f:
            for w in voc:
                wl = list(w)
                e = storage.query_autonomy(wl)
                if not math.isnan(e):
                    f.write("\t".join([delim.join(w), str(e), str(storage.query_count(wl))]) + "\n")

    @staticmethod
    def writePickle(storage, voc, path):
        data = {}
        for w in voc:
            wl = list(w)
            e = storage.query_autonomy(wl)
            if not math.isnan(e):
                data[w] = (e,storage.query_count(wl))
                #f.write("\t".join([w, str(e), str(storage.query_count(wl))]) + "\n")
        with open(path,"wb") as f:
            pickle.dump(data,f)
