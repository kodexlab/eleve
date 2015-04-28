# -*- coding:utf8 -*-
""" :mod:`eleve.storage`
========================

Storage interfaces and abstract class for LM
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

    @abstractmethod
    def __init__(self, path):
        #RMQ: pourquoi un path dans le init (plutot needed just dans load/save)
        #RMQ: en fait le __init__ peut etre laissé complétement libre et dépendant
        # jsute de chaque implémentations
        pass

#RMQ: on ajoute pas un "freq=1" en param ?
#    def add_ngram(self, ngram, freq=1):
    @abstractmethod
    def add_ngram(self, ngram):
        """ Add a newly read ngram to the model's counts
        (will count every (n-k)-grams
        """
        pass

    #RMQ: miss a:
#    @abstractmethod
#    def rm_ngram(self, ngram, freq=1)
#        pass

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

    #RMQ: il manque pas un load ? genre:
#    @abstractmethod
#    @staticmethod
#    def load(path):
#        """ Load model from a file
#        """
#        pass

