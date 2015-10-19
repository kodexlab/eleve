import pytest

from eleve.memory import MemoryTrie

from utils import float_equal, compare_node, generate_random_ngrams
from conftest import all_trie, tested_trie, persistant_trie

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


LE, PETIT, GROS, CHAT, CHIEN, RAT, ET = range(1, 8)

@pytest.mark.parametrize("trie", all_trie, indirect=True)
def test_basic_trie(trie):
    """ Minimal test on simple example
    """
    trie.add_ngram([LE,PETIT,CHAT])
    trie.add_ngram([LE,PETIT,CHIEN])
    trie.add_ngram([LE,PETIT,RAT])
    trie.add_ngram([LE,GROS,RAT])
    assert trie.query_count([LE, PETIT]) == 3
    assert float_equal(trie.query_entropy([LE, PETIT]), 1.584962500721156)
    assert float_equal(trie.query_autonomy([LE, PETIT]), 1.0)
    assert trie.query_count([]) == 4


@pytest.mark.parametrize("trie", all_trie, indirect=True)
def test_clear(trie):
    """ Test the clear method
    """
    trie.add_ngram([LE,PETIT,CHAT])
    assert trie.query_count([LE, PETIT]) == 1
    trie.clear()
    assert trie.query_count([LE, PETIT]) == 0
    trie.add_ngram([LE,GROS,CHAT])
    assert trie.query_count([LE, PETIT]) == 0
    assert trie.query_count([LE, GROS]) == 1


@pytest.mark.parametrize("trie", all_trie, indirect=True)
def test_add_ngram_negativ_freq(trie):
    """ Test to add a ngram with negative freq
    """
    trie.add_ngram([LE,PETIT,CHAT])
    trie.add_ngram([LE,PETIT,CHIEN])
    trie.add_ngram([LE,PETIT,RAT])
    trie.add_ngram([LE,GROS,RAT])
    # test removing a n-gramm
    with pytest.raises(ValueError):
        trie.add_ngram([LE,PETIT,CHAT], -1)
    return
    ## The following is noted here for a futur release, see #18
    assert trie.query_count([LE, PETIT]) == 2
    assert float_equal(trie.query_entropy([LE, PETIT]), 1.0)
    assert float_equal(trie.query_autonomy([LE, PETIT]), 1.0)
    # test removing more than resonable
    trie.add_ngram([LE,PETIT,CHAT], -10)
    assert trie.query_count([LE, PETIT]) == 0


@pytest.mark.parametrize("trie", all_trie, indirect=True)
def test_max_depth(trie):
    """ Test the max depth value
    """
    assert trie.max_depth() == 0
    trie.add_ngram([LE, PETIT, CHAT])
    trie.update_stats()
    print(trie.normalization)
    assert trie.max_depth() == 3
    trie.add_ngram([LE, GROS, CHIEN, ET, LE, PETIT, CHAT])
    assert trie.max_depth() == 7


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


@pytest.mark.parametrize("trie", all_trie, indirect=True)
def test_leaf_to_node(trie):
    """ Test internal converions of a leaf to a node with chidl
    """
    trie.add_ngram([LE, PETIT])
    assert trie.query_count([LE, PETIT]) == 1
    trie.add_ngram([LE, PETIT, CHAT])
    assert trie.query_count([LE, PETIT]) == 2
    assert trie.query_count([LE, PETIT, CHAT]) == 1


@pytest.mark.parametrize("trie", persistant_trie, indirect=True)
def test_reopen(trie):
    """ Test training and the re-openning of persistant trie
    """
    trie.add_ngram([LE,PETIT,CHAT])
    trie.add_ngram([LE,PETIT,CHIEN])
    trie.add_ngram([LE,PETIT,RAT])
    trie.add_ngram([LE,GROS,RAT])
    assert trie.dirty
    # store trie param
    trie_path = trie.path
    trie_class = trie.__class__
    # close and reopen
    trie.close()
    trie = trie_class(trie_path)
    assert trie.dirty
    assert trie.query_count([LE, PETIT]) == 3
    assert float_equal(trie.query_entropy([LE, PETIT]), 1.584962500721156)
    assert float_equal(trie.query_autonomy([LE, PETIT]), 1.0)
    assert trie.query_count([]) == 4
    assert not trie.dirty
    # close and reopen (again)
    trie.close()
    trie = trie_class(trie_path)
    assert not trie.dirty
    assert float_equal(trie.query_autonomy([LE, PETIT]), 1.0)


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

