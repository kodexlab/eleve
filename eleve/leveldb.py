""":mod:`eleve.leveldb`
======================

Provide a Storage (:class:`eleve.leveldb.LeveldbStorage`) and a Trie
(:class:`eleve.leveldb.LeveldbTrie`) that use LevelDB as disk backend.
The implementation over LevelDB is done in python by using :mod:`plyvel`.
"""
import os
import struct
import math
import collections
import logging
import os

import plyvel

from eleve.memory import MemoryTrie, MemoryStorage

NaN = float("nan")

NORMALIZATION_KEY_PREFIX = b"\xff"
NORMALIZATION_PACKER = struct.Struct("<ff")

PACKER = struct.Struct("<Lf")
SEPARATOR = (
    b"\x00"
)  # before every word that is inserted we put that byte, so that they are separated.
SEPARATOR_PLUS_ONE = bytes((SEPARATOR[0] + 1,))


def to_bytes(o):
    """ Encode the object as a bytes object:
    - if it's already a bytes object, don't do nothing
    - else, take its string representation and encode it as a bytes
    """
    return o if type(o) == bytes else str(o).encode()


def ngram_to_key(ngram):
    """ Convert a ngram to a leveldb key (a bytes object).

    The first byte is the length of the ngram, then we have SEPARATOR
    and the bytes representation of the token, for each token.
    """
    assert len(ngram) < 256
    return bytes([len(ngram)]) + b"".join([SEPARATOR + to_bytes(i) for i in ngram])


class Node:
    """ Represents a node of the trie in Leveldb. Loaded by its key.
    Can update its entropy, and save it in leveldb.
    Can list its childs.
    """

    def __init__(self, db, key, data=None):
        """
        :param db: the leveldb object (used to retrieve/save the nodes)
        :param key (bytes): the key of the node in the database
        :param data: should be generally kept as a None.
                     if you have the data, you can pass them as a bytes object.
                     if you pass False, we won't try to retrieve them and assume the node doesn't exists.
        """
        self.db = db
        self.key = key

        if data is None:
            data = db.get(key)

        self.count, self.entropy = PACKER.unpack(data) if data else (0, NaN)

    def iter_childs(self):
        """
        :returns: the childs of the node as other Node objects.
        """
        start = bytes([self.key[0] + 1]) + self.key[1:] + SEPARATOR
        stop = start[:-1] + SEPARATOR_PLUS_ONE
        for key, value in self.db.iterator(start=start, stop=stop):
            yield Node(self.db, key, value)

    def save(self, db=None):
        """ Save the node in the database.

        :param db: You can optionally pass a database if you want to save it
         here instead of the default database.
        """
        value = PACKER.pack(self.count, self.entropy)
        (db or self.db).put(self.key, value)

    def update_entropy(self, terminals):
        """ Update the entropy of the node (and save it if it changed).

        :param terminals: a set of bytes. If a token is inside that set, it will
         count as N different tokens instead of a token
         with count N.
        """
        entropy = 0
        sum_counts = 0
        for child in self.iter_childs():
            if child.count == 0:
                continue
            sum_counts += child.count
            if child.key.split(SEPARATOR)[-1] in terminals:
                entropy += (child.count / self.count) * math.log(self.count, 2)
            else:
                entropy -= (child.count / self.count) * math.log(
                    child.count / self.count, 2
                )
        assert entropy >= 0

        if not sum_counts:
            entropy = NaN
        else:
            assert sum_counts == self.count

        if self.entropy != entropy and not (
            math.isnan(self.entropy) and math.isnan(entropy)
        ):
            self.entropy = entropy
            self.save()


class LeveldbTrie(MemoryTrie):
    def __init__(self, path, terminals=[]):
        """ Create or opent a Trie using leveldb as backend.
        """
        self.path = path
        self.terminals = set(to_bytes(i) for i in terminals)
        self.db = plyvel.DB(
            path,
            create_if_missing=True,
            write_buffer_size=32 * 1024 ** 2,
            # block_size=16*1024,
            # lru_cache_size=512*1024**2,
            # bloom_filter_bits=8,
        )
        # retrieve the normalization constants from leveldb
        self.normalization = []
        depth_level = 0
        while True:
            ndata = self.db.get(NORMALIZATION_KEY_PREFIX + bytes((depth_level,)))
            if ndata is None:
                break
            self.normalization.append(NORMALIZATION_PACKER.unpack(ndata))
            depth_level += 1

        # if no normalization vector founds
        self.dirty = len(self.normalization) == 0

    @property
    def root(self):
        """ Returns root node """
        return Node(self.db, b"\x00")

    def close(self):
        self.db.close()

    def clear(self):
        """ Delete the trie that's in the database. """
        for key in self.db.iterator(include_value=False):
            self.db.delete(key)
        self.dirty = True

    def update_stats(self):
        super(LeveldbTrie, self).update_stats()
        # store normalization vector in DB
        for pseudo_depth, (mean, stdev) in enumerate(self.normalization):
            self.db.put(
                NORMALIZATION_KEY_PREFIX + bytes((pseudo_depth,)),
                NORMALIZATION_PACKER.pack(mean, stdev),
            )
        self.db.compact_range()

    def _check_dirty(self):
        if self.dirty:
            self.update_stats()

    def node(self, ngram):
        return Node(self.db, ngram_to_key(ngram))

    def add_ngram(self, ngram, freq=1):
        if freq <= 0:
            raise ValueError("freq should be larger or equal to 1")
        if len(ngram) == 0:
            logging.warning("Adding empty ngram just do nothing.")
            return

        if not self.dirty:
            self.dirty = True
            self.db.delete(b"\xff\x00")

        b = bytearray(b"\x00")
        w = self.db.write_batch()

        # shortcut : if we encounter a node with a counter to zero, we will
        #            set the node data to False and avoid doing queries for the following nodes.
        create = False

        node = self.root
        node.count += freq
        node.save(w)

        for i in range(1, len(ngram) + 1):
            b[0] = i
            b.extend(SEPARATOR + str(ngram[i - 1]).encode())
            node = Node(self.db, bytes(b), data=(False if create else None))
            if node.count == 0:
                create = True
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
        ev = self.query_ev(ngram)
        if math.isnan(ev):
            return NaN
        try:
            mean, stdev = self.normalization[len(ngram) - 1]
            return (ev - mean) / stdev
        except (ZeroDivisionError, IndexError):
            return NaN


class LeveldbStorage(MemoryStorage):
    def __init__(self, path, default_ngram_length=None):
        """ Initialize the model.

        :param path: Path to the database where to load and store the model.
                     If the path is not existing an empty model will be created.
        :param default_ngram_length: the default maximum length of n-gram beeing
          stored. It will equals 5 for a newly created storage. Note that it may
          be overriden in :func:`add_sentence`.
        """
        self.path = path  # store the path, in RAM, usefull at least for test
        if not os.path.isdir(path):
            os.makedirs(path)
        config_path = path + "/config"
        new_storage = not os.path.isdir(config_path)
        # create/open Storage config/metadata DB
        self.config = plyvel.DB(
            config_path, create_if_missing=True, write_buffer_size=32 * 1024 ** 2
        )
        if new_storage:
            if default_ngram_length is None:
                default_ngram_length = 5
            assert isinstance(default_ngram_length, int) and default_ngram_length > 0
            self.config.put(b"default_ngram_length", str(default_ngram_length).encode())
        self._default_ngram_length = int(self.config.get(b"default_ngram_length"))
        # create/open both trie
        terminals = [self.sentence_start, self.sentence_end]
        self.bwd = LeveldbTrie(path=(path + "/bwd"), terminals=terminals)
        self.fwd = LeveldbTrie(path=(path + "/fwd"), terminals=terminals)
        # TODO: if loading (path exist?) then read the default_ngram_length from DD

    @property
    def default_ngram_length(self):
        return self._default_ngram_length

    def close(self):
        self.config.close()
        self.bwd.close()
        self.fwd.close()
