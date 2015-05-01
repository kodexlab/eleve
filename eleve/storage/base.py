# -*- coding:utf8 -*-
""" Storage interface for LM
"""

from abc import ABCMeta, abstractmethod

# constant for faster access to info type
AUTONOMY = 0
FORWARD_VBE = 1
BACKWARD_VBE = 2
FORWARD_SURPRISE = 3
BACKWARD_SURPRISE = 4

class Storage(object):
    """ Abstract class for LM storage
    """
    __metaclass__ = ABCMeta

    depth = None

    @abstractmethod
    def __init__(self, depth):
        # load/save qui sont dans un format indépendant de l'implémentation de storage
        # ou alors un argument format.
        pass

    @abstractmethod
    def add_ngram(self, ngram, freq=1):
        """ Add a newly read ngram to the model's counts
        (will count every (n-k)-grams
        """
        pass

    @abstractmethod
    def update_stats(self):
        """ Update the statistics of the tree. May be needed before doing queries.
        """
        pass

    def rm_ngram(self, ngram, freq=1):
        return self.add_ngram(ngram, -freq)

    @abstractmethod
    def query_autonomy(self, ngram):
        """ Retrieve the autonomy of the ngram
        """
        pass

    @abstractmethod
    def save(self, path):
        """ Save model to a file
        """
        pass

    @staticmethod
    @abstractmethod
    def load(path):
        """ Load model from a file
        """
        pass


class DualStorage(Storage):
    """ Abstract :class:`.Storage` that use two trees (for forward and backward)
    """
    trie_class = None

    def __init__(self, *args, **kwargs):
        self.fwd_trie = self.trie_class(*args, **kwargs)
        self.bwd_trie = self.trie_class(*args, **kwargs)

    def add_ngram(self, ngram, *args, **kwargs):
        self.fwd_trie.add_ngram(ngram, *args, **kwargs)
        self.bwd_trie.add_ngram(ngram[::-1], *args, **kwargs)
    
    def query_autonomy(self, ngram, *args, **kwargs):
        result_fwd = self.fwd_trie.query_autonomy(ngram, *args, **kwargs)
        result_bwd = self.bwd_trie.query_autonomy(ngram[::-1], *args, **kwargs)
        return (result_fwd + result_bwd) / 2.
     
    def query_ev(self, ngram, *args, **kwargs):
        result_fwd = self.fwd_trie.query_ev(ngram, *args, **kwargs)
        result_bwd = self.bwd_trie.query_ev(ngram[::-1], *args, **kwargs)
        return (result_fwd + result_bwd) / 2.

    def query_node(self, ngram, *args, **kwargs):
        result_fwd = self.fwd_trie.query_node(ngram, *args, **kwargs)
        result_bwd = self.bwd_trie.query_node(ngram[::-1], *args, **kwargs)
        return tuple((i + j) / 2. for i, j in zip(result_fwd, result_bwd))

    def update_stats(self, *args, **kwargs):
        self.fwd_trie.update_stats(*args, **kwargs)
        self.bwd_trie.update_stats(*args, **kwargs)

    def save(self, path):
        self.fwd_trie.save(path + ".fwd")
        self.bwd_trie.save(path + ".bwd")

