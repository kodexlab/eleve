# -*- coding:utf8 -*-

import numpy as np
import codecs

import eleve.storage as storage
from . import tokenisation
import eleve.nlptypes as NLP


def segmente(sequence, model, nmax=6):
    u"""
    segmente une liste de formes <sequence> en utilisant utilisant un <model>
    """
    def a(w):
        l = len(w)
        if l > nmax:
            raise ValueError
        a = model.query(storage.AUTONOMY, w, failwith=np.float("-inf"))
        return a * l
    if len(sequence) == 1:
        return sequence
    table = np.empty((len(sequence)+1, 2), dtype=object)
    table[0, 0] = [0]  # segmentation
    table[0, 1] = 0.  # score
    for pos in xrange(1, len(sequence)+1):
        scores = np.empty(min(nmax, pos))
        segmentations = np.empty(min(nmax, pos), dtype=object)
        for i, prev in enumerate(xrange(max(0, pos-nmax), pos)):
            segmentations[i] = table[prev, 0] + [pos]
            scores[i] = table[prev, 1] + a(sequence[prev:pos])
        imax = np.argmax(scores)
        table[pos, 0] = segmentations[imax]
        table[pos, 1] = scores[imax]
    result = []
    curs = 0
    for boundary_position in table[-1, 0]:
        result.append(sequence[curs:boundary_position])
        curs = boundary_position
    return result[1:]
    #return [b in table[-1, 0] for b in xrange(len(sequence)+1)]

def preprocess_segment_corpus_gen(text, engine=None, returnType="text", sep=""):
    if engine is None:
        engine = tokenisation.engine_nothing
    for tokseq in engine.apply(text):
        pass


def preprocess_segment(sentence, engine, model):
    """
    preprocess one <sentence> with <engine> and segment the relevant tokens
    """
    result = []
    for tok in engine(sentence):
        if tok.pos == "unsegmented":
            result.extend([ NLP.Wordform("".join(w),"Word", w)  for w in segmente(tok.tokens, model, model.nmax)])
        else:
            result.append(tok)
    return result


def train_model(model, corpus_path, engine):
    f = codecs.open(corpus_path, "r", "utf8")
    for l in f:
        l = l.strip()
        for tok in engine(l):
            if tok.pos == "unsegmented":
                model.read_ngram(tok.form)
    model.compute_entropies()
    model.normalise()

        
