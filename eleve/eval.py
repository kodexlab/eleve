# -*- coding: utf8 -*-
import codecs


from . import segmentation
from . import tokenisation 



def positions_of_tokens(tokens):
    begin = 0
    result = set()
    for tok in tokens:
        end = begin + len(tok.form)
        result.add((begin, end))
        begin = end
    return result

def boundaries_positions(tokens_test, tokens_gold, typed=False):
    begin = 0
    begin_gold = 0
    r_test = set()
    r_gold = set()
    r_test_others = set()
    r_gold_others = set()
    i = 0
    tokgold = tokens_gold[i]
    for tok in tokens_test[:-1]:
        end = begin + len(tok.form)
        if typed:
            pass
        else:
            r_test.add(end)
        while begin_gold + len(tokgold.form) < end:
            begin_gold += len(tokgold.form)
            r_gold.add(begin_gold)
            i += 1
            tokgold = tokens_gold[i]
        begin = end



def config_no_preproc(train_path):
    segmenteur = segmentation.Segmenteur()
    segmenteur.train(train_path, True, preproc=tokenisation.engine_nothing)
    return segmenteur

def config_no_preproc(train_path):
    segmenteur = segmentation.Segmenteur()
    segmenteur.train(train_path, True, preproc=tokenisation.engine_default)
    return segmenteur

def config_rnn(train_path):
    segmenteur = segmentation.Segmenteur()
    segmenteur.train_arpa(train_path, True, engine=tokenisation.engine_nothing)
    return segmenteur

def config_rnn_preproc(train_path):
    segmenteur = segmentation.Segmenteur()
    segmenteur.train_arpa(train_path, True, engine=tokenisation.engine_default)
    return segmenteur


# TODO: path a Segmenteur rather than a training corpus
def eval(segmenteur, gold_path, engine, n=6, engine_test=None):
    good = 0.
    test = 0.
    gold = 0.
    corpus = codecs.open(gold_path, "r", "utf8")
    for line in corpus:
        line = line.strip()
        gold_tokens = [tokenisation.Token(list(forme), "Word") for forme in line.split()]
        test_tokens = segmenteur.segment_one(line.replace(" ", ""), preproc=engine_test, returnType='obj')
        gold_pos = positions_of_tokens(gold_tokens)
        test_pos = positions_of_tokens(test_tokens)
        good += len(gold_pos.intersection(test_pos))
        test += len(test_pos)
        gold += len(gold_pos)
    pr = good / test if test > 0. else 0.
    ra = good / gold if gold > 0. else 0.
    f = 2*pr*ra/(pr + ra)
    return {'p': pr, 'r': ra, 'f': f}

    

