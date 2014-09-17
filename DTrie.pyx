# -*- coding: utf-8 -*-
"""
Created on Sun May 12 14:13:46 2013

@author: pierre
"""
import sys
import numpy as np

cdef class Trie:
    cdef public int count
    cdef public float entropy
    cdef public object children
    cdef object default

    def __init__(self):
        self.count = 0
        self.entropy = 0.
        self.children = {}
        self.default = {}


    cdef Trie find(self,ngram):
        cdef int ch
        cdef Trie fils
        if len(ngram) == 0:
            return self
        ch = ngram[0]
        if not ch in self.children:
            return None
        fils = self.children[ch]
        return fils.find(ngram[1:])




    def entropie(self, boundaryMode="None", last_punct=0):
        cdef int ch
        cdef int l
        cdef Trie fils
        cdef float tot
        values, puncts = [], []
        for ch, fils in self.children.iteritems():
            if ch > last_punct:
                values.append(fils.count)
            else:
                puncts.append(fils.count)
        if boundaryMode == "None" and puncts != []:
            values.extend(puncts)
        elif boundaryMode == "unique" and puncts != []:
            nocc_aux_bornes = np.sum(puncts)
            values.extend([1. for _ in xrange(nocc_aux_bornes)])
        elif boundaryMode == "max":
            print u"boundary mode MAX pas implémenté dans entropie()"
            sys.exit(1)
        l = len(values)
        if l == 0:
            return np.nan
        elif l == 1:
            return 0.
        else:
            tot = np.sum(values)
            return - sum([(v / tot) * np.log2(v / tot) for v in values])
    
    def entropie_from_pcond(self):
        cdef int ch
        cdef int l
        cdef Trie fils
        values = []
        for fils in self.children.itervalues():
            if fils.entropy != 0.:
                values.append(fils.entropy)
        l = len(values)
        if l == 0:
            return np.nan
        elif l == 1:
            return 0.
        else:
            return - sum([p * np.log2(p) for p in values])



    def compute_entropy_variation(self, boundaryMode="unique",last_punct=0):
        cdef int ch
        cdef Trie fils
        cdef Trie current
        def rec(current, prev_h):
            for ch, fils in current.children.iteritems():
                h = fils.entropie(boundaryMode, last_punct)
                if h == 0. and prev_h == 0.:
                    fils.entropy = np.nan
                else:
                    fils.entropy = h - prev_h
                rec(fils, h)
        rec(self, self.entropie(boundaryMode, last_punct)) #  0.)

    def compute_entropy_variation_from_pcond(self):
        cdef int ch
        cdef Trie fils
        cdef Trie current
        def rec(current, prev_h):
            for ch, fils in current.children.iteritems():
                h = fils.entropie_from_pcond()
                if h == 0. and prev_h == 0.:
                    fils.entropy = np.nan
                else:
                    fils.entropy = h - prev_h
                rec(fils, h)
        rec(self, self.entropie_from_pcond())

    def compute_entropy(self, boundaryMode="unique", last_punct=0):
        cdef int ch
        cdef Trie fils
        cdef Trie current
        def rec(current):
            for ch, fils in current.children.items():
                h = fils.entropie(boundaryMode, last_punct)
                if not np.isnan(h):
                    fils.entropy = h
                else:
                    fils.entropy = 0.
                rec(fils)
        self.entropy = self.entropie(boundaryMode, last_punct)
        f = open("/tmp/h","a")
        f.write("h0=%f\n" %(self.entropy,))
        f.close()
        rec(self)
        return self.entropy

    def prune(self):
        cdef int ch
        cdef Trie fils
        cdef Trie current
        def rec(current):
            for ch, fils in current.children.items():
                if len(fils.children) == 1:
                    k,v = fils.children.items()[0]
                    if v.count == 1:
                        fils.children = {}
                rec(fils)
        rec(self)


    def getVBEsByLength(self, int n):
        u"""
        retourne un tableau contenant mots et VBE pour une certaine longueur n
        """
        cdef int k, gram
        cdef Trie current, fils

        liste = []
        def rec(current, k):
            if k == n - 1:
                for fils in current.children.itervalues():
                    #w = acc + [gram]
                    if not np.isnan(fils.entropy):
                        liste.append(fils.entropy)
                    #else:
                    #    liste.append(0.)
            else:
                for gram, fils in current.children.iteritems():
                    rec(fils, k+1)
        rec(self,0)
        return np.array(liste)

    def updateVBE(self,int n,float m, float sd):
        u"""
        normalise les n-grams avec une moyenne m et un écart-type sd
        """
        cdef Trie current,fils
        cdef int k,ng

        def rec(current, k):
            if k == n -1:
                for ng,fils in current.children.items():
                    fils.entropy = (fils.entropy - m) / sd
            else:
                for fils in current.children.itervalues():
                    rec(fils, k+1)
        rec(self, 0)


    def normalise_types(self, int nmax, centralf=np.mean, spreadf=lambda x:1.):
        cdef int k
        for k in xrange(1, nmax + 1):
            values_r = self.getVBEsByLength(k) # liste de valeurs de VBE
            if len(values_r) > 0:
                m = centralf(values_r)
                sd = spreadf(values_r)
                del values_r
                print k,m,sd
                self.updateVBE(k, m, sd)
                self.default[k] = - m / sd
            else:
                print "pas de val",k



cdef class DTrie:
    cdef public Trie fwd
    cdef public Trie bwd
    cdef int nmax
    cdef int ntypes

    def __init__(self,int nmax):
        self.nmax = nmax
        self.fwd = Trie()
        self.bwd = Trie()


    cdef __set_rec(self, Trie trie, ch, apres, back, float pcond):
        cdef Trie nt
        cdef Trie data
        cdef int popIndex

        if back:
            popIndex = -1
        else:
            popIndex = 0
        if ch in trie.children:
            data = trie.children[ch]
            if apres == []:
                data.entropy = pcond
            else:
                next_char = apres.pop(popIndex)
                self.__set_rec(data, next_char, apres, back, pcond)
        else:
            nt = Trie()
            nt.count = 0
            nt.children = {}
            if apres == []:
                nt.entropy = pcond
                trie.children[ch] = nt
            else:
                trie.children[ch] = nt
                next_char = apres.pop(popIndex)
                self.__set_rec(nt, next_char, apres, back, pcond)

    cdef __add_rec(self, Trie trie, avant, ch, apres,int length, back):
        cdef Trie nt
        cdef Trie data
        cdef int popIndex

        if back:
            popIndex = -1
        else:
            popIndex = 0
        if ch in trie.children:
            data = trie.children[ch]
            data.count = data.count + 1
            if back:
                avant.insert(0,ch)
            else:
                avant.append(ch)
            if apres != []:
                next_char = apres.pop(popIndex)
                self.__add_rec(data, avant, next_char, apres, length + 1, back)
        else:
            if back:
                avant.insert(0,ch)
            else:
                avant.append(ch)
            nt = Trie()
            nt.count = 1
            nt.children = {}
            trie.children[ch] = nt
            if apres != [] and length < 4:
                next_char = apres.pop(popIndex)
                self.__add_rec(nt, avant, next_char, apres, length + 1, back)


    def add(self, ngram, doBackward=False):
        cdef int popIndex
        if doBackward:
            first = ngram.pop(-1)
            self.__add_rec(self.bwd, [], first, ngram, 1, doBackward)
        else:
            first = ngram.pop(0)
            self.__add_rec(self.fwd, [], first, ngram, 1, doBackward)

    def set_pcond(self, ngram, pcond, doBackward=False):
        cdef int popIndex
        if not pcond > 0.:
            return
        if doBackward:
            first = ngram.pop(-1)
            self.__set_rec(self.bwd, first, ngram, doBackward, pcond)
        else:
            first = ngram.pop(0)
            self.__set_rec(self.fwd, first, ngram, doBackward, pcond)

    def query_forward(self,ngram, failwith=None):
        cdef Trie t
        t = self.fwd.find(ngram)
        if not t:
            return failwith
        return t.entropy

    def query_count_forward(self,ngram, failwith=0):
        cdef Trie t
        t = self.fwd.find(ngram)
        if not t:
            return failwith
        return t.count

    def query_backward(self,ngram, failwith=None):
        cdef Trie t
        ngram = list(reversed(ngram))
        t = self.bwd.find(ngram)
        if not t:
            return failwith
        return t.entropy

    def query_count_backward(self,ngram, failwith=0):
        cdef Trie t
        ngram = list(reversed(ngram))
        t = self.bwd.find(ngram)
        if not t:
            return failwith
        return t.count

    def iterate_on(self,t):
        result = []
        def aux(cur,acc):
            result.append((acc,cur.count,cur.entropy))
            for g,suiv in cur.children.items():
                aux(suiv,acc+[g])
        for g,child in t.children.items():
            aux(child,[g])
        return result


    def iterate(self):
        it = self.iterate_on(self.fwd)
        for (ng,count,entrop_f) in it:
            entrop_b = self.query_backward(ng, failwith=np.nan)
            yield (ng,count,entrop_b, entrop_f)

    def compute_entropy_variation(self, boundaryMode="unique", last_punct=0):
        self.fwd.compute_entropy_variation(boundaryMode, last_punct)
        self.bwd.compute_entropy_variation(boundaryMode, last_punct)

    def compute_entropy_variation_from_pcond(self):
        self.fwd.compute_entropy_variation_from_pcond()
        self.bwd.compute_entropy_variation_from_pcond()

    def compute_entropy(self, boundaryMode="unique", last_punct=0):
        print "h0f", self.fwd.compute_entropy(boundaryMode, last_punct)
        return self.bwd.compute_entropy(boundaryMode, last_punct)


    def normalise_types(self, int nmax, centralf=np.mean, spreadf=lambda x:1.):
        self.fwd.normalise_types(nmax, centralf=np.mean, spreadf=spreadf)
        self.bwd.normalise_types(nmax, centralf=np.mean, spreadf=spreadf)

    def prune(self):
        self.fwd.prune()
        self.bwd.prune()


