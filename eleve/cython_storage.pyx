# distutils: language = c++
import math
import logging

from libc.math cimport log2
from libcpp.unordered_map cimport unordered_map
from libcpp.set cimport set as cset
from libcpp.vector cimport vector
from libcpp.utility cimport pair

from libc.stdlib cimport malloc, free
from cython.operator import postincrement, dereference

import pickle

NaN = float("nan")

cdef struct node:
    int count
    float entropy
    unordered_map[int, node*] *children


cdef node* createNode():
    cdef node* r = <node*> malloc(sizeof(node))
    r.count = 0
    r.children = new unordered_map[int, node*]()
    return r


cdef void freeNodeRec(node* n):
    cdef node *c
    cdef unordered_map[int,node*].iterator it = n.children.begin()
    while it != n.children.end():
        freeNodeRec(dereference(it).second)
        it = n.children.erase(it)
    free(n.children)
    free(n)

cdef void updateEntropy(node* n, cset[int] breaks):
    cdef float entropy = 0.0
    cdef float total = 0 #n.count
    cdef float c
    cdef int token
    cdef node* child
    cdef unordered_map[int,node*].iterator it = n.children.begin()
    while it != n.children.end():
        total += dereference(it).second.count
        postincrement(it)
    it = n.children.begin()
    while it != n.children.end():
        token = dereference(it).first
        child = dereference(it).second
        c = child.count
        if breaks.count(token) > 0:
            entropy += (c/total) * log2(total)
        else:
            entropy -= (c / total) * log2(c / total)
        postincrement(it)
    n.entropy = entropy

cdef int pruneNodeHappax(node* n):
    cdef int sum = 0
    cdef node* child
    cdef unordered_map[int,node*].iterator it = n.children.begin()
    while it != n.children.end():
        child = dereference(it).second
        if child.count == 1:
            freeNodeRec(child)
            it = n.children.erase(it)
            sum += 1
        else:
            sum += pruneNodeHappax(child)
            if child.count == 0:
                freeNodeRec(child)
                it = n.children.erase(it)
            else:
                postincrement(it)
    n.count -= sum
    return sum

cdef int pruneNode(node* n,int qnt):
    cdef int sum = 0
    cdef node* child
    cdef unordered_map[int,node*].iterator it = n.children.begin()
    while it != n.children.end():
        child = dereference(it).second
        child.count -= qnt
        if child.count <= 0:
            freeNodeRec(child)
            it = n.children.erase(it)
            sum += 1
        else:
            pruneNode(child, qnt)
            postincrement(it)
    return sum



cdef void updateEntropyRec(node* n, cset[int] breaks):
    cdef unordered_map[int,node*].iterator it = n.children.begin()
    updateEntropy(n, breaks)
    while it != n.children.end():
        child = dereference(it).second
        updateEntropyRec(child, breaks)
        postincrement(it)



cdef class CythonTrie:
    cdef node *root;
    cdef cset[int] breaks;
    cdef dict vbe
    cdef list normalization
    cdef bint dirty
    cdef dict encoder

    __slots__ = ["root", "vbe", "normalization", "dirty", "encoder"]

    def __init__(self, terminals=frozenset()):
        self.root = createNode()
        self.vbe = {}
        self.normalization = []
        #self.terminals = frozenset(terminals)
        self.encoder = {}
        self.dirty = True
        self.fill_breaks(terminals)

    cdef fill_breaks(self, terminals):
        for t in terminals:
            self.breaks.insert(self.encode_token(t))


    cdef _get_voc_rec(self, node* n, prefix, decoder, acc):
        cdef unordered_map[int,node*].iterator it = n.children.begin()
        cdef node *child
        while it != n.children.end():
            token = dereference(it).first
            child = dereference(it).second
            count = child.count
            ngram = prefix + [decoder[token]]
            acc.append(ngram)
            acc = self._get_voc_rec(child, ngram, decoder, acc)
            postincrement(it)
        return acc

    def get_voc(self):
        decoder = {v:k for k,v in self.encoder.items()}
        return self._get_voc_rec(self.root, [], decoder, [])

    def prune(self, qnt=1):
        pruneNode(self.root, qnt)
        self.dirty = True


    cdef _update_stats_rec(self, parent_entropy, depth, node* currentNode):
        """ Recurively update both entropy and normalization vector
        """
        # extend normalization vector if needed
        cdef unordered_map[int,node*].iterator it
        cdef node *child

        while len(self.normalization) < depth:
            self.normalization.append((0.0, 0.0, 0))
        # if MemoryLeaf nothing else should be done
        if currentNode.children.size() == 0:
            return
        updateEntropy(currentNode, self.breaks)
        #node.update_entropy(self.terminals)
        # update entropy variation mean and std if possible (not NaN)
        if (
            depth > 0
            and not math.isnan(currentNode.entropy)
            and (currentNode.entropy or parent_entropy)
        ):
            ev = currentNode.entropy - parent_entropy
            mean, stdev, count = self.normalization[depth - 1]
            old_mean = mean
            count += 1
            mean += (ev - old_mean) / count
            stdev += (ev - old_mean) * (ev - mean)
            self.normalization[depth - 1] = mean, stdev, count
        # recurifs calls
        it = currentNode.children.begin()
        while it != currentNode.children.end():
            child = dereference(it).second
            self._update_stats_rec(currentNode.entropy, depth + 1, child)
            postincrement(it)

    def update_stats(self):
        if not self.dirty:
            return
        self.normalization = []
        self._update_stats_rec(NaN, 0, self.root)
        for pseudo_depth, (mean, _stdev, count) in enumerate(self.normalization):
            stdev = math.sqrt(_stdev / (count or 1))
            self.normalization[pseudo_depth] = (mean, stdev)
        self.dirty = False

    cdef _rec_add_ngram(self, node* n, ngram, int freq):
        cdef node* child
        n.count += freq
        if len(ngram) > 0 :
            head = ngram[0]
            tail = ngram[1:]
            if n.children.count(head) == 0:
                child = createNode()
                dereference(n.children)[head] = child
            else:
                child = n.children.at(head)
            self._rec_add_ngram(child, tail, freq)


    def encode_token(self, tok):
        if tok in self.encoder:
            return self.encoder[tok]
        else:
            code = len(self.encoder)
            self.encoder[tok] = code
            return code

    # todo: encode ngram into a C array or C++ vector
    def encode_ngram(self, ngram):
        encoded = []
        return [self.encode_token(tok) for tok in ngram]

    def add_ngram(self, ngram, freq=1):
        self._rec_add_ngram(self.root, self.encode_ngram(ngram), freq)


    cdef node* _lookup(self, ngram, node* current_node):
        if len(ngram) == 0:
            return current_node
        else:
            head = ngram[0]
            tail = ngram[1:]
            if current_node.children.count(head) == 0:
                return NULL
            else:
                return self._lookup(tail, current_node.children.at(head))

    cdef (node*, node*) _lookup2(self, ngram):
        cdef node* n;
        cdef node* last_node;
        n = self.root
        last_node = n
        while ngram:
            last_node = n
            if n.children.count(ngram[0]) == 0:
                return (NULL, NULL)
            n = n.children.at(ngram[0])
            ngram = ngram[1:]
        return (last_node, n)

    def query_count(self, ngram):
        cdef node *n;
        ngram = self.encode_ngram(ngram)
        n = self._lookup(ngram, self.root)
        if n:
            return n.count
        else:
            return 0

    def query_entropy(self, ngram):
        cdef node *n;
        ngram = self.encode_ngram(ngram)
        n = self._lookup(ngram, self.root)
        if n:
            return n.entropy
        else:
            return float("nan")

    def query_ev(self, ngram):
        """ Query for the branching entropy variation.

        :param ngram: A list of tokens.
        :returns: A float, that can be NaN if it is not defined.
        """
        cdef node *n;
        cdef node *last_node;
        ngram = self.encode_ngram(ngram)
        self._check_dirty()
        if not ngram:
            return float("nan")
        last_node, n = self._lookup2(ngram)
        if (not last_node) or (not n):
            return float("nan")
        if not math.isnan(n.entropy) and (
                n.entropy != 0 or last_node.entropy != 0
        ):
            return n.entropy - last_node.entropy
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
