import struct
import math
import collections
import logging

import plyvel

NaN = float('nan')
PACKER = struct.Struct('<Lf')

def to_bytes(o):
    return o if type(o) == bytes else str(o).encode()

def ngram_to_key(ngram):
    return bytes([len(ngram)]) + b''.join([b'@' + to_bytes(i) for i in ngram])

class Node:
    def __init__(self, db, key, data=None):
        self.db = db
        self.key = key

        if data is None:
            data = db.get(key)

        self.count, self.entropy = (0, NaN) if data is None else PACKER.unpack(data)

    def childs(self):
        start = bytes([self.key[0] + 1]) + self.key[1:] + b'@'
        stop = start[:-1] + b'A'
        for key, value in self.db.iterator(start=start, stop=stop):
            yield Node(self.db, key, value)

    def save(self, db=None):
        if db is None:
            db = self.db
        value = PACKER.pack(self.count, self.entropy)
        db.put(self.key, value)

    def update_entropy(self, terminals):
        if self.count == 0:
            self.entropy = NaN
            return

        entropy = 0
        sum_counts = 0
        for child in self.childs():
            if child.count == 0:
                continue
            sum_counts += child.count
            if child.key.split(b'@')[-1] in terminals:
                entropy += (child.count / self.count) * math.log2(self.count)
            else:
                entropy -= (child.count / self.count) * math.log2(child.count / self.count)
        assert entropy >= 0

        if not sum_counts:
            entropy = NaN
        else:
            assert sum_counts == self.count

        if self.entropy != entropy and not(math.isnan(self.entropy) and math.isnan(entropy)):
            self.entropy = entropy
            self.save()
    
class LevelTrie:
    def __init__(self, path="/tmp/level_trie", terminals=['^', '$'], delete=False):
        self.terminals = set(to_bytes(i) for i in terminals)

        self.db = plyvel.DB(path,
                create_if_missing=True,
                #write_buffer_size=32*1024**2,
                #block_size=16*1024,
                #lru_cache_size=512*1024**2,
                #bloom_filter_bits=8,
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

    def update_stats(self):
        if not self.dirty:
            return

        def rec(parent_entropy, depth, node):
            node.update_entropy(self.terminals)

            if not math.isnan(node.entropy) and (node.entropy or parent_entropy):
                ev = node.entropy - parent_entropy

                mean, stdev, count = self.normalization[depth]
                old_mean = mean
                count += 1
                mean += (ev - old_mean) / count
                stdev += (ev - old_mean)*(ev - mean)
                self.normalization[depth] = mean, stdev, count

            for child in node.childs():
                rec(node.entropy, depth + 1, child)

        self.normalization = collections.defaultdict(lambda: (0.,0.,0))
        rec(NaN, 0, Node(self.db, b'\x00'))
        for k, (mean, stdev, count) in self.normalization.items():
            self.normalization[k] = (mean, math.sqrt(stdev / (count if count else 1)), count)

        self.dirty = False
        
    def _check_dirty(self):
        if self.dirty:
            logging.warning("Updating the tree statistics (update_stats method), as we query it while dirty. This is a slow operation.")
            self.update_stats()

    def node(self, ngram):
        return Node(self.db, ngram_to_key(ngram))

    def add_ngram(self, ngram, freq=1):
        self.dirty = True
        b = bytearray(b'\x00')
        w = self.db.write_batch()

        node = Node(self.db, b'\x00')
        node.count += freq
        node.save(w)

        for i in range(1, len(ngram) + 1):
            b[0] = i
            b.extend(b'@' + str(ngram[i - 1]).encode())
            node = Node(self.db, bytes(b))
            node.count += freq
            node.save(w)

        w.write()

    def query_count(self, ngram):
        return self.node(ngram).count

    def query_entropy(self, ngram):
        self._check_dirty()
        return self.node(ngram).entropy

    def query_ev(self, ngram):
        self._check_dirty()
        if not ngram:
            return NaN
        node = self.node(ngram)
        if math.isnan(node.entropy):
            return NaN
        parent = self.node(ngram[:-1])
        if node.entropy != 0 or parent.entropy != 0:
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

