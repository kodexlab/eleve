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
    def query_autonomy(self, ngram):
        """ Retrieve the autonomy of the ngram
        """
        pass

    @abstractmethod
    def save(self, path):
        """ Save model to a file
        """
        pass

    @classmethod
    @abstractmethod
    def load(path):
        """ Load model from a file
        """
        pass

