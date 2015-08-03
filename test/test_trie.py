import pytest
import random
import tempfile
import os

from eleve.memory import MemoryTrie
from eleve.cstorages import MemoryTrie as CMemoryTrie

def float_equal(a, b):
    return (a != a and b != b) or abs(a - b) < 1e-6

def generate_random_ngrams():
    """ Generate list of random n-grams (of int)
    """
    depth = random.randint(3,4)
    m = []

    def add(prefix):
        for i in range(int(random.expovariate(0.2) + 1)):
            k = int(random.expovariate(0.2))
            if len(prefix) < depth - 1:
                add(prefix + [k])
            else:
                m.append(prefix + [k])

    add([])
    random.shuffle(m)
    return (depth, m)

def compare_nodes(ngram, ref_trie, test_trie):
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

@pytest.mark.parametrize("trie_class", [CMemoryTrie])
def test_trie_class(trie_class, reference_class=MemoryTrie):
    """ Compare implementation against reference class (on random ngrams lists)
    """
    depth, ngrams = generate_random_ngrams()
    test_trie = trie_class()
    ref_trie = reference_class()

    test_trie.clear()
    ref_trie.clear()
    for n in ngrams:
        test_trie.add_ngram(n)
        ref_trie.add_ngram(n)
        compare_nodes(n, test_trie, ref_trie) # slow

    for n in ngrams:
        for i in range(len(n)):
            compare_nodes(n[:i+1], test_trie, ref_trie)
            compare_nodes(n[:i] + [420001337], test_trie, ref_trie) # try a non-existent node
        compare_nodes(n + [420001337], test_trie, ref_trie) # try a non-existent node

    compare_nodes([], test_trie, ref_trie)
    compare_nodes([420001337] * 10, test_trie, ref_trie)

@pytest.mark.parametrize("trie_class", [MemoryTrie])
def test_basic_trie(trie_class):
    """ Minimal test on simple example
    """
    m = trie_class()
    m.clear()
    m.add_ngram(('le','petit','chat'))
    m.add_ngram(('le','petit','chien'))
    m.add_ngram(('le','gros','chien'))
    assert m.query_count(('le', 'petit')) == 2
    assert m.query_entropy(('le', 'petit')) == 1.0
    assert m.query_count(None) == 3
    assert m.query_count(('le', 'petit')) != m.query_count(('le', 'gros'))
    m.add_ngram(('le','petit','chat'), freq=-1)
    assert m.query_count(('le', 'petit')) == m.query_count(('le', 'petit'))
    assert m.query_entropy(('le', 'petit')) == m.query_entropy(('le', 'petit'))

#TODO: test de remove
#FIXME: on dirait que ça checke pas les cas ou l'entropie est pas définie (genre une feuille avec un fils, tout ça)
