# -*- coding:utf8 -*-
""" Storage interface for LM
"""

from abc import ABCMeta, abstractmethod

class Storage(metaclass=ABCMeta):
    """ Abstract class for LM storage
    """
    depth = None

    @abstractmethod
    def __init__(self, depth):
        # load/save qui sont dans un format indépendant de l'implémentation de storage
        # ou alors un argument format.
        pass

    @abstractmethod
    def add_sentence(self, sentence, freq=1):
        """ Add a sentence.
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

    def __init__(self, depth, *args, **kwargs):
        self.depth = depth
        self.fwd_trie = self.trie_class(depth, *args, **kwargs)
        self.bwd_trie = self.trie_class(depth, *args, **kwargs)

    def add_sentence(self, token_list, *args, **kwargs):
        token_list = [None] + token_list + [None]
        for i in range(len(token_list) - 1):
            ngram = token_list[i:i+self.depth]
            self.fwd_trie.add_ngram(ngram, *args, **kwargs)
        token_list = token_list[::-1]
        for i in range(len(token_list) - 1):
            ngram = token_list[i:i+self.depth]
            self.bwd_trie.add_ngram(ngram, *args, **kwargs)
    
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
