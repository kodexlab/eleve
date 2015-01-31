#!/usr/bin/env python
# -*- coding:utf8 -*-

import sys
import os
import numpy as np
import codecs
import cPickle as pickle
from collections import namedtuple

from eleve.DTrie_sqlite import DTrie as DTrieSQL
from eleve.DTrie import DTrie


from . import tokenisation

#atomic datatype for Binary Tree unsupervised parsing
#left and right should contains a BTNode or a terminal token
BNode = namedtuple("BTNode","form left right")




class LanguageModel:
    def __init__(self, nmax=6, dbpath=None, boundaryToken="$$$"):
        if dbpath is None:
            print "inmem"
            self.DT = DTrie(nmax)
        if dbpath and os.path.exists(dbpath + ".lm"):
            self.load(dbpath + ".lm")
            self.DT = DTrieSQL(nmax, dbpath=dbpath + ".sqlite")
        else:
            if dbpath:
                self.DT = DTrieSQL(nmax, dbpath=dbpath + ".sqlite")
            self.nmax = nmax
            self.encodeur = {boundaryToken: 0}
            self.decodeur = [boundaryToken]
            self.ntypes = 1
            self.last_punct = 0
        self.cache = {}
        self.cached = False

    def encode_ngram(self, ngram):
        return [self.encode(tok) for tok in ngram]

    def encode_ngram_with_boundaries(self, ngram):
        codes = [self.encode(tok) for tok in ngram]
        codes.insert(0, 0)
        codes.append(0)
        return codes

    def encode(self, token, add=True, failwith=None):
        if token in self.encodeur:
            return self.encodeur[token]
        if not add:
            if failwith:
                return failwith
            print "pb avec", token
            raise ValueError
        self.encodeur[token] = self.ntypes
        self.decodeur.append(token)
        self.ntypes += 1
        return self.ntypes - 1

    def add_ngram(self, ngram):
        ngram = self.encode_ngram_with_boundaries(ngram)
        for left in range(0, len(ngram)):
            right = min(left + self.nmax, len(ngram))
            self.DT.add(ngram[left:right+1])
        for right in range(1, len(ngram)):
            left = max(0, right - self.nmax)
            self.DT.add(ngram[left:right+1], doBackward=True)

    def set_from_arpa(self, ngram, pcond, doBackward=False):
        ngram = self.encode_ngram(ngram)
        if doBackward:
            ngram = list(reversed(ngram))
        self.DT.set_pcond(ngram, pcond, doBackward)

    def query_forward(self, ngram, failwith=None):
        return self.DT.query_forward(tuple(ngram), failwith)

    def query_backward(self, ngram, failwith=None):
        return self.DT.query_backward(tuple(ngram), failwith)

    def query_count(self, ngram):
        #ngram = self.encode_ngram(ngram)
        return self.DT.query_count_forward(ngram)

    def autonomie_of_coded_tuple(self, ngram, failwith=None, f=lambda x, y: x + y):
        left = self.query_backward(ngram, failwith=failwith)
        right = self.query_forward(ngram, failwith=failwith)
        if left == failwith or right == failwith:
            return failwith
        return f(left, right)

    def autonomie(self, word, failwith=None, f=lambda x, y: x + y):
        #if word in self.cache:
        #    return self.cache[word]
        ngram = tuple(self.encode_ngram(word))
        v = self.autonomie_of_coded_tuple(ngram, failwith=failwith, f=f)
        #self.cache[word] = v
        return v

    def compute_entropy_variation(self, boundaryMode="unique"):
        self.DT.compute_entropy_variation(boundaryMode, self.last_punct)

    def compute_entropy_variation_from_arpa(self):
        self.DT.compute_entropy_variation_from_pcond()

    def compute_entropy(self, boundaryMode="unique"):
        print self.DT.compute_entropy(boundaryMode, self.last_punct)

    def normalise_types(self, centralf=np.mean, spreadf=lambda x: 1.):
        self.DT.normalise_types(self.nmax, centralf=np.mean, spreadf=spreadf)

    def prune(self):
        self.DT.prune()
    
    def parse_encoded_sequence(self, sequence, seg_init=None):
        u"""
        arborise une sequence de token en supprimant des coupures une par une
        """
        if seg_init is None:
            segmentation = np.empty((len(sequence)-1,), dtype=bool)
            segmentation.fill(True)  # segmentation à chaque token
        else:
            assert(len(sequence) == a.shape[0])
            segmentation = seg_init
        scores = np.zeros((len(sequence)-1,))
        
        def a(w):
            l = len(w)
            fwd = self.query_forward(w, failwith=np.nan)
            bwd = self.query_backward(w, failwith=np.nan)
            if np.isnan(bwd) or np.isnan(fwd):
                return np.nan
            else:
                return (fwd + bwd) * l

        def score(prefix,suffix): 
            apref = a(prefix)
            asuf = a(suffix)
            aw = a(prefix + suffix)
            if all([not np.isnan(x) for x in [apref,asuf,aw]]):
                return aw - apref - asuf
            else:
                return np.float("-inf")

        def get_bornes(i, seg):
            debut = i
            fin = i
            while debut > 0:
                debut -=1
                if seg[debut]:
                    break
            while fin < len(seg):
                fin += 1
                if seg[fin]:
                    break
            return (debut, fin)

        def score_line(segmentation, segref):
            for i in xrange(len(segmentation)):
                if not segmentation[i]:
                    scores[i] = np.nan
                else:
                    debut, fin = get_bornes(i, segref)
                    pfx = sequence[debut:i]
                    sfx = sequence[i:fin]
                    scores[i] = score(pfx, sfx)



        nboundaries = np.sum(segmentation)
        while nboundaries > 0:
            score_line(segmentation, segmentation)
            if all([np.isneginf(x) for x in scores]):
                score_line(segmentation, segmentation_origine)
            iscores = np.argsort(scores)
            pos = iscores[-1]







    

    def segmente_encoded_sequence(self, sequence, af=lambda x, y: x+y):
        u"""
        segmente une sequence déjà encodée (tableau d'entiers)
        retourne une liste de boolen (coupure/non coupure avant chaque position)
        """
        def a(w):
            l = len(w)
            if l > self.nmax:
                return np.float("-inf")
            fwd = self.query_forward(w, failwith=np.nan)
            bwd = self.query_backward(w, failwith=np.nan)
            if fwd is None or bwd is None or np.isnan(fwd) or np.isnan(bwd):
                return -100.
                return np.float("-inf")
            return af(fwd, bwd)*l

        if len(sequence) == 1:
            return [True, True]

        table = np.empty((len(sequence)+1, 2), dtype=object)
        table[0, 0] = [0]  # segmentation
        table[0, 1] = 0.  # score
        for pos in xrange(1, len(sequence)+1):
            scores = np.empty(min(self.nmax, pos))
            segmentations = np.empty(min(self.nmax, pos), dtype=object)
            for i, prev in enumerate(xrange(max(0, pos-self.nmax), pos)):
                segmentations[i] = table[prev, 0] + [pos]
                scores[i] = table[prev, 1] + a(sequence[prev:pos])
            imax = np.argmax(scores)
            table[pos, 0] = segmentations[imax]
            table[pos, 1] = scores[imax]
        return [b in table[-1, 0] for b in xrange(len(sequence)+1)]

    def segment_corpus_with_preprocessing(self, text, engine=None, returnType="text", sep=""):
        if engine is None:
            engine = tokenisation.engine_nothing
        for tokseq in engine.apply(text):
            result = []
            for tok in tokseq:
                if tok.pos == "unsegmented":
                    result.extend(self.segmente(tok.form))
                else:
                    result.append(tok)
            if returnType == "text":
                yield " ".join([sep.join(t.form) for t in result])
            elif returnType == "tagged":
                yield " ".join(["%s/%s" % (sep.join(t.form), t.pos) for t in result])
            else:
                yield result

    def segmente(self, sequence, af=lambda x, y: x+y):
        encseq = self.encode_ngram_with_boundaries(sequence)
        seg = self.segmente_encoded_sequence(encseq, af=af)
        result = []
        cursor = 0
        for i in xrange(1, len(sequence)+1):
            if seg[i + 1]:
                result.append(tokenisation.Wordform(u"".join(sequence[cursor:i]), "Word", tokens=sequence[cursor:i]))
                cursor = i
        return result

    def segmente_raw(self, sequence, af=lambda x, y: x+y):
        encseq = self.encode_ngram_with_boundaries(sequence)
        seg = self.segmente_encoded_sequence(encseq, af=af)
        result = []
        cursor = 0
        for i in xrange(1, len(sequence)+1):
            if seg[i + 1]:
                result.append(sequence[cursor:i])
                cursor = i
        return result

    def iter_model(self, seuil=0., sep=u""):
        for (ng, count, g, d) in self.DT.iterate():
            if g is None or d is None:
                continue
            a = g + d
            if seuil is None or a > seuil:
                yield {'forme': sep.join([self.decodeur[c] for c in ng]),
                       'count': count,
                       'autonomie': a}

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

    def load_arpa(self, fwd, bwd):
        def load_one(data, backward):
            l = data.next().strip()
            if l != "\\data\\":
                print 1, l
                print "error: not in arpa format", l
                print "\n".join(data)
                sys.exit(1)
            l = data.next().strip()
            while l != "":
                l = data.next().strip()
            self.data = []
            for o in range(1, self.nmax+2):
                l = data.next().strip()
                if not (l == "\\%d-grams:" % (o,)):
                    print 3, l
                    print "error: not in arpa format", l
                    sys.exit(1)
                l = data.next().strip()
                while l != "":
                    fields = l.split("\t")
                    if len(fields) > 1:
                        pcond = 10**np.float(fields[0])
                        ngram = fields[1].split(" ")
                        self.set_from_arpa(ngram, pcond, backward)
                    l = data.next().strip()
        load_one(fwd, False)
        load_one(bwd, True)
    
    def read_iterator(self, iterator, engine=None, target="unsegmented"):
        if engine is None:
            engine = tokenisation.engine_nothing
        for tokseq in engine.apply(iterator):
            for tok in tokseq:
                if tok.pos != target:
                    pass
                else:
                    self.add_ngram(tok.form)

    def read_corpus(self, infile, enc="utf8", preproc=None, nline=None):
        self._read_builtin(infile, enc, engine=preproc, nline=nline)

    def _read_builtin(self, path, enc, engine=None, nline=None, target="unsegmented",sep="\t"):
        if engine is None:
            engine = tokenisation.engine_nothing
        nl = 0
        infile = codecs.open(path, "r", enc)
        for tokseq in engine.apply(infile):
            for tok in tokseq:
                if tok.pos != target:
                    pass
                else:
                    self.add_ngram(tok.form)
            if nline and nl >= nline:
                break
        infile.close()

    def read_raw(self, infile, enc="utf8", preproc=lambda x: x.strip().replace(" ", ""), nline=None):
        f = codecs.open(infile, "r", enc)
        nl = 0
        for l in f:
            nl += 1
            #print l
            preprocessed = list(l.strip())
            self.add_ngram(preprocessed)
            if nline and nl >= nline:
                break
        f.close()
