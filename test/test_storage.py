import pytest
import random
import tempfile
import os

from eleve.incremental_memory import IncrementalMemoryStorage
from eleve.memory import MemoryStorage

def generate_random_ngrams():
    """ Generate list of random n-grams (of int)
    """
    depth = random.randint(2,4)
    m = []

    def add(prefix):
        for i in range(int(random.expovariate(0.1) + 1)):
            k = int(random.gauss(0, 7))
            if len(prefix) < depth - 1:
                add(prefix + [k])
            else:
                m.append(prefix + [k])

    add([])
    random.shuffle(m)
    return (depth, m)


def compare_tries(ref_trie, test_trie):
    """ fails if two tries are different (on count, entropy, ...)
    """
    for ngram in ref_trie:
        count_ref, entropy_ref = ref_trie.query_node(ngram)
        count_test, entropy_test = test_trie.query_node(ngram)
        assert count_ref == count_test
        assert abs(entropy_ref - entropy_test) < 1e-6, (entropy_ref, entropy_test)

        ev_ref = ref_trie.query_ev(ngram)
        ev_test = test_trie.query_ev(ngram)
        assert abs(ev_ref - ev_test) < 1e-6, (ev_ref, ev_test)

        autonomy_ref = ref_trie.query_autonomy(ngram, z_score=False)
        autonomy_test = test_trie.query_autonomy(ngram, z_score=False)
        assert abs(autonomy_ref - autonomy_test) < 1e-6, (autonomy_ref, autonomy_test)

        # FIXME: test avec normalisation par la variance
        """
        autonomy_ref = ref_trie.query_autonomy(ngram, z_score=True)
        autonomy_test = test_trie.query_autonomy(ngram, z_score=True)
        assert abs(autonomy_ref - autonomy_test) < 1e-6, (autonomy_ref, autonomy_test)
        """

@pytest.mark.parametrize("storage_class", [IncrementalMemoryStorage])
def test_storage_class(storage_class, reference_class=MemoryStorage):
    """ Compare implementation against reference class (on random ngrams lists)
    """
    depth, ngrams = generate_random_ngrams()
    test_trie = storage_class(depth)
    ref_trie = reference_class(depth)
    for n in ngrams:
        test_trie.add_ngram(n)
        ref_trie.add_ngram(n)
    compare_tries(ref_trie, test_trie)

@pytest.mark.parametrize("storage_class", [MemoryStorage, IncrementalMemoryStorage])
def test_save_load_storage_class(storage_class):
    """ Test save/load methods (on random ngrams lists)
    """
    depth, ngrams = generate_random_ngrams()
    test_trie = storage_class(depth)
    for n in ngrams:
        test_trie.add_ngram(n)
    # test load/save
    with tempfile.TemporaryDirectory(prefix='eleve_') as t:
        fn = os.path.join(t, 'test_storage')
        test_trie.save(fn)
        reloaded_trie = storage_class.load(fn)
    compare_tries(test_trie, reloaded_trie)

@pytest.mark.parametrize("storage_class", [MemoryStorage, IncrementalMemoryStorage])
def test_basic_storage(storage_class):
    """ Minimal test on simple example
    """
    m = storage_class(3)
    m.add_ngram(('le','petit','chat'))
    m.add_ngram(('le','petit','chien'))
    m.add_ngram(('le','gros','chien'))
    assert m.query_node(('le', 'petit')) == (2, 1.0)
    assert m.query_node(None)[0] == 3
    assert m.query_node(('le', 'petit')) != m.query_node(('le', 'gros'))
    m.add_ngram(('le','petit','chat'), -1)
    assert m.query_node(('le', 'petit')) == m.query_node(('le', 'gros'))


#TODO: test de remove

