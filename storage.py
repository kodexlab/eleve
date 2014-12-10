# -*- coding:utf8 -*-

from abc import ABCMeta, abstractmethod
import numpy as np
import pickle

from DTrie import DTrie


# constant for faster access to info type
AUTONOMY = 0
FORWARD_VBE = 1
BACKWARD_VBE = 2
FORWARD_SURPRISE = 3
BACKWARD_SURPRISE = 5

class Storage(object):
    """
    abstract class for LM storage
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def read_ngram(self, ngram):
        """
        add a newly read ngram to the model's counts
        (will count every (n-k)-grams
        """
        pass

    @abstractmethod
    def estimate_probabilities(self):
        """
        estimate conditional probabilities from stored counts
        """
        pass

    @abstractmethod
    def set_probabilities(self, ngram, pcond, is_backward=False):
        """
        set the conditional probability value 
        (for exemple from a smoothed arpa file)
        """
        pass

    @abstractmethod
    def compute_entropies(self):
        """
        compute branching entropies from conditional probabilities
        """
        pass

    @abstractmethod
    def normalise(self):
        """
        normalise the stored entropies values
        """
        pass

    @abstractmethod
    def query(self, what, ngram):
        """
        retrive <what> value for <ngram>
        """
        pass

    @abstractmethod
    def save(self, path):
        """
        save model to a file
        """
        pass

    @abstractmethod
    def load(self, path):
        """
        load model from a file
        """
        pass

class MemoryStorage(Storage):
    """
    LM stored in RAM
    """

    def __init__(self, nmax=6, boundaryToken=u"\ue000"):
        super(MemoryStorage, self).__init__() 
        self.nmax = nmax
        self.encodeur = {boundaryToken:0}
        self.decodeur = [boundaryToken]
        self.ntypes = 1
        self.DT = DTrie(nmax)

    def encode(self, token, add=True, failwith=None):
        if token in self.encodeur:
            return self.encodeur[token]
        if not add:
            if failwith:
                return failwith
            else:
                raise ValueError
        self.encodeur[token] = self.ntypes
        self.decodeur.append(token)
        self.ntypes += 1
        return self.ntypes -1

    def encode_ngram_with_boundaries(self, ngram):
        codes = [0]
        codes.extend([self.encode(tok) for tok in ngram])
        codes.append(0)
        return codes

    def read_ngram(self, ngram):
        ngram = self.encode_ngram_with_boundaries(ngram)
        for left in range(0, len(ngram)):
            right = min(left + self.nmax, len(ngram))
            self.DT.add(ngram[left:right+1])
        for right in range(1, len(ngram)):
            left = max(0, right - self.nmax)
            self.DT.add(ngram[left:right+1], doBackward=True)

    def estimate_probabilities(self):
        #TODO: implementer ça dans DTrie
        raise NotImplementedError

    def set_probabilities(self, ngram, pcond, is_backward=False):
        #TODO: modifier DTrie pour calculer l'entropie en 2 temps
        raise NotImplementedError

    def compute_entropies(self):
        self.DT.compute_entropy()
        self.DT.compute_entropy_variation()

    def normalise(self):
        self.DT.normalise_types(self.nmax, np.mean, np.std)

    def query(self, what, ngram, failwith=None):
        coded = [self.encode(tok) for tok in ngram]
        if what == AUTONOMY:
            try:
                nRVBE = self.DT.query_backward(coded)
                nLVBE = self.DT.query_forward(coded)
                return nRVBE + nLVBE
            except:
                if failwith:
                    return failwith
                else:
                    raise ValueError
        elif what == FORWARD_VBE:
            return self.DT.query_forward(coded)
        elif what == BACKWARD_VBE:
            return self.DT.query_backward(coded)
        raise NotImplementedError

    def save(self, outfile):
        f = open(outfile, "w")
        pickle.dump((self.encodeur,
                     self.decodeur,
                     self.nmax,
                     self.DT,
                     self.last_punct,
                     self.ntypes), f, pickle.HIGHEST_PROTOCOL)
        f.close()

    def load(self, infile):
        print "loading", infile
        f = open(infile, "r")
        (self.encodeur,
         self.decodeur,
         self.nmax,
         self.DT,
         self.last_punct,
         self.ntypes) = pickle.load(f)
        f.close()

