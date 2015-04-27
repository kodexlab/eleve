# -*- coding:utf8 -*-

from abc import ABCMeta, abstractmethod

# constant for faster access to info type
AUTONOMY = 0
FORWARD_VBE = 1
BACKWARD_VBE = 2
FORWARD_SURPRISE = 3
BACKWARD_SURPRISE = 4

class Storage(object):
    """
    abstract class for LM storage
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(self, path):
        pass

    @abstractmethod
    def add_ngram(self, ngram):
        """
        add a newly read ngram to the model's counts
        (will count every (n-k)-grams
        """
        pass

    @abstractmethod
    def query_autonomy(self, ngram):
        """
        retrieve the autonomy of the ngram
        """
        pass

    @abstractmethod
    def save(self, path):
        """
        save model to a file
        """
        pass
