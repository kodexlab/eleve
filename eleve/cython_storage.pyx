# distutils: language = c++
import math
import logging

from libcpp.unordered_map cimport unordered_map

import pickle

NaN = float("nan")

cdef class Node:
    cdef int count
    cdef float entropy
    cdef dict children # todo: try with unordered_map

    __slots__ = ["count", "entropy", "children"]

    def __init__(self):
        self.children = {}
        self.count = 0
        self.entropy = -100.0

    def getCount(self):
        return self.count

    def update_entropy(self, terminals: frozenset):
        """ Update the entropy of the node.

        :param terminals: a set of bytes. If a token is inside that set, it will
         count as N different tokens instead of a token with count N.
        """
        cdef Node child;
        cdef float entropy;
        cdef int sum_counts;

        entropy = 0
        sum_counts = 0
        for token, child in self.children.items():
            if child.getCount() == 0:
                continue
            sum_counts += child.getCount()
            if token in terminals:
                entropy += (child.getCount() / self.count) * math.log(self.count, 2)
            else:
                entropy -= (child.getCount() / self.count) * math.log(
                    child.getCount() / self.count, 2
                )
        if not sum_counts:
            entropy = NaN
        else:
            assert sum_counts == self.count
        self.entropy = entropy


class CythonTrie:
    __slots__ = ["root", "vbe", "normalization", "terminals", "dirty"]

    def __init__(self, terminals=frozenset()):
        self.root = Node()
        self.vbe = {}
        self.normalization = []
        self.terminals = frozenset(terminals)
        self.dirty = True

    def prune(self, minus=1):
        pass

    def _update_stats_rec(self, parent_entropy, depth, node: Node):
        """ Recurively update both entropy and normalization vector
        """
        # extend normalization vector if needed
        while len(self.normalization) < depth:
            self.normalization.append((0.0, 0.0, 0))
        # if MemoryLeaf nothing else should be done
        if len(node.children) == 0:
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
        for child in node.children.values():
            self._update_stats_rec(node.entropy, depth + 1, child)

    def update_stats(self):
        if not self.dirty:
            return
        self.normalization = []
        self._update_stats_rec(NaN, 0, self.root)
        for pseudo_depth, (mean, _stdev, count) in enumerate(self.normalization):
            stdev = math.sqrt(_stdev / (count or 1))
            self.normalization[pseudo_depth] = (mean, stdev)
        self.dirty = False

    def _rec_add_ngram(self, node: Node, ngram, freq):
        node.count += freq
        if len(ngram) > 0 :
            head = ngram[0]
            tail = ngram[1:]
            if head not in node.children:
                node.children[head] = Node()
            self._rec_add_ngram(node.children[head], tail, freq)


    def add_ngram(self, ngram, freq=1):
        self._rec_add_ngram(self.root, ngram, freq)


    def _lookup(self, ngram, current_node: Node):
        if len(ngram) == 0:
            return current_node
        else:
            head = ngram[0]
            tail = ngram[1:]
            if head not in current_node.children:
                return None
            else:
                return self._lookup(tail, current_node.children[head])

    def _lookup2(self, ngram):
        cdef Node node;
        cdef Node last_node;
        node = self.root
        last_node = node
        while ngram:
            last_node = node
            node = node.children[ngram[0]]
            ngram = ngram[1:]
        return (last_node, node)

    def query_count(self, ngram):
        cdef Node node;
        node = self._lookup(ngram, self.root)
        if node:
            return node.count
        else:
            return 0

    def query_ev(self, ngram):
        """ Query for the branching entropy variation.

        :param ngram: A list of tokens.
        :returns: A float, that can be NaN if it is not defined.
        """
        cdef Node node;
        cdef Node last_node;
        self._check_dirty()
        if not ngram:
            return float("nan")
        try:
            last_node, node = self._lookup2(ngram)
        except (KeyError, AttributeError):
            return float("nan")
        if not math.isnan(node.entropy) and (
                node.entropy != 0 or last_node.entropy != 0
        ):
            return node.entropy - last_node.entropy
        return float("nan")

    def _check_dirty(self):
        if self.dirty:
            logging.warning(
                "Updating the tree statistics (update_stats method), as we query it while dirty. This is a slow operation."
            )
            self.update_stats()

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
