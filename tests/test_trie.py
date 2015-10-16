import pytest

from eleve.memory import MemoryTrie

from utils import float_equal, compare_node, generate_random_ngrams
from conftest import all_trie, tested_trie

def compare_nodes(ngrams, ref_trie, test_trie):
    # compare root
    compare_node([], ref_trie, test_trie)
    # compare random node, may not existe (check exception)
    compare_node([420001337] * 10, ref_trie, test_trie)
    # compare all ngrams
    for n in ngrams:
        for i in range(len(n)):
            compare_node(n[:i+1], ref_trie, test_trie)
            # try a non-existent node:  should raise exception in both case
            compare_node(n[:i] + [420001337], ref_trie, test_trie)
        compare_node(n + [420001337], ref_trie, test_trie) # try a non-existent node


@pytest.mark.parametrize("trie", all_trie, indirect=True)
def test_basic_trie(trie):
    """ Minimal test on simple example
    """
    trie.clear()
    LE, PETIT, GROS, CHAT, CHIEN, RAT = range(1, 7)

    trie.add_ngram([LE,PETIT,CHAT])
    trie.add_ngram([LE,PETIT,CHIEN])
    trie.add_ngram([LE,PETIT,RAT])
    trie.add_ngram([LE,GROS,RAT])
    assert trie.query_count([LE, PETIT]) == 3
    assert float_equal(trie.query_entropy([LE, PETIT]), 1.584962500721156)
    assert float_equal(trie.query_autonomy([LE, PETIT]), 1.0)
    assert trie.query_count([]) == 4

    # test removing a n-gramm
    trie.add_ngram([LE,PETIT,CHAT], -1)
    assert trie.query_count([LE, PETIT]) == 2
    assert float_equal(trie.query_entropy([LE, PETIT]), 1.0)
    assert float_equal(trie.query_autonomy([LE, PETIT]), 1.0)


@pytest.mark.parametrize("trie", all_trie, indirect=True)
def test_robustness(trie):
    """ Test robustness of Tries
    """
    trie.clear()
    #FIXME: see https://git.kodexlab.com/kodexlab/eleve/issues/16
    with pytest.raises(ValueError):
        trie.add_ngram([])
    with pytest.raises(ValueError):
        trie.add_ngram([0x42])


@pytest.mark.parametrize("trie", tested_trie, indirect=True)
def test_versus_ref_on_random(trie, reference_class=MemoryTrie):
    """ Compare implementation against reference class (on random ngrams lists)
    """
    trie.clear()
    ref_trie = reference_class()
    ref_trie.clear()
    ngrams = generate_random_ngrams(nb=100, size=5)
    for i, n in enumerate(ngrams):
        trie.add_ngram(n)
        ref_trie.add_ngram(n)
        if i % (len(ngrams)//10) == 0: # check 10 times
            compare_nodes(ngrams, ref_trie, trie)
    compare_nodes(ngrams, ref_trie, trie)

