import struct
import math
import collections
import logging
import sys
from contextlib import contextmanager

import plyvel

NaN = float('nan')
PACKER = struct.Struct('<Lf')

def to_bytes(o):
    return o if type(o) == bytes else str(o).encode()

def ngram_to_key(ngram):
    return bytes([len(ngram)]) + b''.join([b'@' + to_bytes(i) for i in ngram])

def ngram_to_next_key(ngram):
    return bytes([len(ngram) + 1]) + b''.join([b'@' + to_bytes(i) for i in ngram]) + b'@'

class Node:
    def __init__(self, trie, ngram, data=None):
        self.trie = trie
        self.ngram = ngram

        if data is None:
            data = trie.db.get(ngram_to_key(ngram))
        if data is None:
            self.count, self.entropy = 0, NaN
        else:
            self.count, self.entropy = PACKER.unpack(data)

        self.old_count, self.old_entropy = self.count, self.entropy

    def childs(self):
        start = ngram_to_next_key(self.ngram)
        stop = start[:-1] + b'A' #
        for key, value in self.trie.db.iterator(start=start, stop=stop):
            ngram = self.ngram + [key.split(b'@')[-1]]
            yield Node(self.trie, ngram, value)

    def calculate_entropy(self, terminals):
        if self.count == 0:
            self.entropy = NaN
            return

        entropy = 0
        sum_counts = 0
        for child in self.childs():
            sum_counts += child.count
            if child.ngram[-1] in terminals:
                entropy += (child.count / self.count) * math.log2(self.count)
            else:
                entropy -= (child.count / self.count) * math.log2(child.count / self.count)
        assert entropy >= 0
        assert sum_counts == self.count or sum_counts == 0
        self.entropy = entropy if sum_counts else NaN
    
    def save(self):
        if self.count != self.old_count or (self.entropy != self.old_entropy and not (math.isnan(self.entropy) and math.isnan(self.old_entropy))):
            value = PACKER.pack(self.count, self.entropy)
            self.trie.db.put(ngram_to_key(self.ngram), value)
    
class LevelTrie:
    def __init__(self, path, terminals=['^', '$'], delete=False):
        self.terminals = set(to_bytes(i) for i in terminals)

        self.db = plyvel.DB(path,
                create_if_missing=True,
                #write_buffer_size=16*1024**2,
                #block_size=16*1024,
                #lru_cache_size=512*1024**2,
                #bloom_filter_bits=10,
        )

        if delete:
            for key in self.db.iterator(include_value=False):
                self.db.delete(key)
        self.normalization = collections.defaultdict(lambda: (0.,0.,0))
        self.dirty = False
        self.path = path

    def clear(self):
        self.db.close()
        self.__init__(self.path, self.terminals, delete=True)

    def _debug_dump(self):
        print('-- BEGIN DEBUG DUMP --', file=sys.stderr)
        for key, value in self.db.iterator(fill_cache=False):
            print(key, value, file=sys.stderr)
        print('-- END DEBUG DUMP --', file=sys.stderr)

    def update_stats(self):
        def rec(parent_entropy, depth, ngram):
            with self.node(ngram) as node:
                node.calculate_entropy(self.terminals)

                if not math.isnan(node.entropy) and (node.entropy or parent_entropy):
                    ev = node.entropy - parent_entropy

                    mean, stdev, count = self.normalization[depth]
                    old_mean = mean
                    count += 1
                    mean += (ev - old_mean) / count
                    stdev += (ev - old_mean)*(ev - mean)
                    self.normalization[depth] = mean, stdev, count

                for child in node.childs():
                    rec(node.entropy, depth + 1, child.ngram)

        self.normalization = collections.defaultdict(lambda: (0.,0.,0))
        rec(NaN, 0, [])
        for k, (mean, stdev, count) in self.normalization.items():
            self.normalization[k] = (mean, math.sqrt(stdev / (count if count else 1)), count)

        self.dirty = False
        
    def _check_dirty(self):
        if self.dirty:
            logging.warning("Updating the tree statistics (update_stats method), as we query it while dirty. This is a slow operation.")
            self.update_stats()

    @contextmanager
    def node(self, ngram):
        try:
            n = Node(self, ngram)
            yield n
        finally:
            n.save()

    def add_ngram(self, ngram, freq=1):
        self.dirty = True

        for i in range(len(ngram) + 1):
            n = ngram[:i]

            with self.node(n) as node:
                node.count += freq

    def query_count(self, ngram):
        with self.node(ngram) as node:
            return node.count

    def query_entropy(self, ngram):
        self._check_dirty()
        with self.node(ngram) as node:
            return node.entropy

    def query_ev(self, ngram):
        self._check_dirty()
        if not ngram:
            return NaN
        with self.node(ngram) as node, self.node(ngram[:-1]) as parent:
            if not math.isnan(node.entropy) and (node.entropy != 0 or parent.entropy != 0):
                return node.entropy - parent.entropy
            return NaN

    def query_autonomy(self, ngram):
        self._check_dirty()
        mean, stdev, count = self.normalization[len(ngram)]
        if not count:
            return NaN
        ev = self.query_ev(ngram)
        if math.isnan(ev):
            return NaN
        try:
            return (ev - mean) / stdev
        except ZeroDivisionError:
            return NaN

