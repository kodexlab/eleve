import pytest
import random
import tempfile
import os

from eleve.memory import MemoryStorage
from eleve.neo4j import Neo4jStorage
from eleve.merge import MergeStorage

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
    
    ngrams = set(map(tuple, ref_trie))
    for i, n in enumerate(set(ngrams)):
        if i > 20:
            break
        ngrams.add(tuple(n[:-1] + ('nonexistent',)))
        ngrams.add(tuple(n[:-2] + ('nonexistent',)))
        ngrams.add(tuple(n[:-2] + ('nonexistent','nonexistent')))

    for ngram in ngrams:
        count_ref, entropy_ref = ref_trie.query_node(ngram)
        count_test, entropy_test = test_trie.query_node(ngram)
        assert count_ref == count_test
        assert abs(entropy_ref - entropy_test) < 1e-6

        ev_ref = ref_trie.query_ev(ngram)
        ev_test = test_trie.query_ev(ngram)
        assert abs(ev_ref - ev_test) < 1e-6

        autonomy_ref = ref_trie.query_autonomy(ngram, z_score=False)
        autonomy_test = test_trie.query_autonomy(ngram, z_score=False)
        assert abs(autonomy_ref - autonomy_test) < 1e-6

        try:
            autonomy_ref = ref_trie.query_autonomy(ngram, z_score=True)
            autonomy_test = test_trie.query_autonomy(ngram, z_score=True)
            assert abs(autonomy_ref - autonomy_test) < 1e-6
        except ZeroDivisionError:
            pass # in case the variance is null, because we are on the last level...

@pytest.mark.parametrize("storage_class", [Neo4jStorage, MergeStorage])
def test_storage_class(storage_class, reference_class=MemoryStorage):
    """ Compare implementation against reference class (on random ngrams lists)
    """
    depth, ngrams = generate_random_ngrams()
    test_trie = storage_class(depth, 'test').clear()
    ref_trie = reference_class(depth, 'test').clear()
    for n in ngrams:
        test_trie.add_ngram(n, 1)
        ref_trie.add_ngram(n, 1)
    compare_tries(ref_trie, test_trie)

@pytest.mark.parametrize("storage_class", [MemoryStorage])
def test_save_load_trie(storage_class):
    """ Test save/load methods (on random ngrams lists)
    """
    depth, ngrams = generate_random_ngrams()
    test_trie = storage_class(depth)
    for n in ngrams:
        test_trie.add_ngram(n, 1)
    # test load/save
    with tempfile.TemporaryDirectory(prefix='eleve_') as t:
        fn = os.path.join(t, 'test_storage')
        test_trie.save(fn)
        reloaded_trie = storage_class.load(fn)
    compare_tries(test_trie, reloaded_trie)

@pytest.mark.parametrize("storage_class", [MemoryStorage, Neo4jStorage, MergeStorage])
def test_basic_storage(storage_class):
    """ Minimal test on simple example
    """
    m = storage_class(3, 'test').clear()
    m.add_ngram(('le','petit','chat'), 1)
    m.add_ngram(('le','petit','chien'), 1)
    m.add_ngram(('le','gros','chien'), 1)
    assert m.query_node(('le', 'petit')) == (2, 1.0)
    assert m.query_node(None)[0] == 3
    assert m.query_node(('le', 'petit'))[0] != m.query_node(('le', 'gros'))[0]
    m.add_ngram(('le','petit','chat'), 1 ,-1)
    assert m.query_node(('le', 'petit')) == m.query_node(('le', 'gros'))


#TODO: test de remove
#TODO: test des postings
