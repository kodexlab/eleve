# -*- coding:utf8 -*-
""" Storage interface for LM
"""

from abc import ABCMeta, abstractmethod

class Storage(metaclass=ABCMeta):
    """ Abstract class for LM storage
    """
    depth = None

    @abstractmethod
    def __init__(self, depth, path):
        # load/save qui sont dans un format indépendant de l'implémentation de storage
        # ou alors un argument format.
        pass

    @abstractmethod
    def clear(self):
        """ Clear the storage. """
        return self

    @abstractmethod
    def add_ngram(self, ngram, freq=1):
        """ Add a sentence.
        """
        pass

    def update_stats(self):
        """ Update the statistics of the tree. May be needed before doing queries.
        """
        return

    def rm_ngram(self, ngram, freq=1):
        return self.add_ngram(ngram, -freq)

    @abstractmethod
    def query_autonomy(self, ngram, z_score):
        """ Retrieve the autonomy of the ngram
        """
        pass

    @abstractmethod
    def query_node(self, ngram):
        """ Return the (count, entropy) for a ngram """
        pass

    @abstractmethod
    def query_postings(self, ngram):
        """ Return an iterator to tuples (docid, frequency).
        Works only for leaf nodes ATM """
        pass
