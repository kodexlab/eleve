import pytest
import random
import tempfile
import os
import gc

from eleve.memory import MemoryTrie
from eleve.leveldb import LevelTrie
from eleve.c_leveldb.cleveldb import LeveldbTrie as CLevelTrie
from eleve.cstorages import MemoryTrie as CMemoryTrie

def float_equal(a, b):
    return (a != a and b != b) or abs(a - b) < 1e-4

def generate_random_ngrams():
    """ Generate list of random n-grams (of int)
    """
    depth = random.randint(3,5)
    m = []

    def add(prefix):
        for i in range(int(random.expovariate(0.1) + 1)):
            k = int(random.expovariate(0.1))
            if len(prefix) < depth - 1:
                add(prefix + [k])
            else:
                m.append(prefix + [k])

    add([])
    random.shuffle(m)
    return m

def compare_node(ngram, ref_trie, test_trie):
    """
    fails if the results of any measure is different for the query of a specific ngram
    """

    measures = ['query_count', 'query_entropy', 'query_ev', 'query_autonomy']

    for measure in measures:
        try:
            m_ref = getattr(ref_trie, measure)(ngram)
        except Exception as e:
            with pytest.raises(type(e)):
                getattr(test_trie, measure)(ngram)
        else:
            m_test = getattr(test_trie, measure)(ngram)
            assert float_equal(m_ref, m_test), "%s different for ngram %s" % (measure, ngram)

def compare_nodes(ngrams, ref_trie, test_trie):
    for n in ngrams:
        for i in range(len(n)):
            compare_node(n[:i+1], ref_trie, test_trie)
            compare_node(n[:i] + [420001337], ref_trie, test_trie) # try a non-existent node
        compare_node(n + [420001337], ref_trie, test_trie) # try a non-existent node

    compare_node([], ref_trie, test_trie)
    compare_node([420001337] * 10, ref_trie, test_trie)

@pytest.mark.parametrize("trie_class", [LevelTrie, CMemoryTrie, CLevelTrie])
def test_trie_class(trie_class, reference_class=MemoryTrie):
    """ Compare implementation against reference class (on random ngrams lists)
    """
    gc.collect()
    ngrams = generate_random_ngrams()
    test_trie = trie_class()
    ref_trie = reference_class()

    test_trie.clear()
    ref_trie.clear()

    for i, n in enumerate(ngrams):
        test_trie.add_ngram(n)
        ref_trie.add_ngram(n)
        if i % (len(ngrams) // 3) == 0:
            compare_nodes(ngrams, ref_trie, test_trie)
    compare_nodes(ngrams, ref_trie, test_trie)

@pytest.mark.parametrize("trie_class", [MemoryTrie, LevelTrie, CMemoryTrie, CLevelTrie])
def test_basic_trie(trie_class):
    """ Minimal test on simple example
    """
    gc.collect()
    m = trie_class()
    m.clear()

    LE, PETIT, GROS, CHAT, CHIEN = range(1, 6)

    m.add_ngram([LE,PETIT,CHAT])
    m.add_ngram([LE,PETIT,CHIEN])
    m.add_ngram([LE,GROS,CHIEN])
    assert m.query_count([LE, PETIT]) == 2
    assert m.query_entropy([LE, PETIT]) == 1.0
    assert m.query_count([]) == 3
    assert m.query_count([LE, PETIT]) != m.query_count([LE, GROS])
    m.add_ngram([LE,PETIT,CHAT], -1)
    assert m.query_count([LE, PETIT]) == m.query_count([LE, GROS])
    assert m.query_entropy([LE, PETIT]) == m.query_entropy([LE, GROS])

