import pytest
import random
import tempfile
import os

from eleve.incremental_memory import IncrementalMemoryStorage
from eleve.memory import MemoryStorage

def generate_random_ngrams():
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
    for ngram in ref_trie:
        count_ref, entropy_ref = ref_trie.query_node(ngram)
        count_test, entropy_test = test_trie.query_node(ngram)
        assert count_ref == count_test
        assert abs(entropy_ref - entropy_test) < 1e-6, (entropy_ref, entropy_test)

        ev_ref = ref_trie.query_ev(ngram)
        ev_test = test_trie.query_ev(ngram)
        assert abs(ev_ref - ev_test) < 1e-6, (ev_ref, ev_test)

        autonomy_ref = ref_trie.query_autonomy(ngram)
        autonomy_test = test_trie.query_autonomy(ngram)
        assert abs(autonomy_ref - autonomy_test) < 1e-6, (autonomy_ref, autonomy_test)

        # FIXME
        """
        autonomy_ref = ref_trie.query_autonomy(ngram, lambda x: x)
        autonomy_test = test_trie.query_autonomy(ngram, lambda x: x)
        assert abs(autonomy_ref - autonomy_test) < 1e-6, (autonomy_ref, autonomy_test)
        """

@pytest.mark.parametrize("storage_class", [IncrementalMemoryStorage])
def test_storage_class(storage_class, reference_class=MemoryStorage):
    depth, ngrams = generate_random_ngrams()
    test_trie = storage_class(depth)
    ref_trie = reference_class(depth)
    for n in ngrams:
        test_trie.add_ngram(n)
        ref_trie.add_ngram(n)
    compare_tries(ref_trie, test_trie)
    with tempfile.TemporaryDirectory(prefix='eleve_') as t:
        fn = os.path.join(t, 'test_storage')
        test_trie.save(fn)
        test_trie = storage_class.load(fn)
    compare_tries(ref_trie, test_trie)

def test_memory_storage():
    depth, ngrams = generate_random_ngrams()
    ref_trie = MemoryStorage(depth)
    for n in ngrams:
        ref_trie.add_ngram(n)
    with tempfile.TemporaryDirectory(prefix='eleve_') as t:
        fn = os.path.join(t, 'test_storage')
        ref_trie.save(fn)
        test_trie = MemoryStorage.load(fn)
        compare_tries(ref_trie, test_trie)

@pytest.mark.parametrize("storage_class", [MemoryStorage, IncrementalMemoryStorage])
def test_basic_storage(storage_class):
    m = storage_class(3)
    m.add_ngram(('le','petit','chat'))
    m.add_ngram(('le','petit','chien'))
    m.add_ngram(('le','gros','chien'))
    m.update_stats()
    assert m.query_node(('le', 'petit')) == (2, 1.0)
    assert m.query_node(None)[0] == 3
    assert m.query_node(('le', 'petit')) != m.query_node(('le', 'gros'))
    m.add_ngram(('le','petit','chat'), -1)
    m.update_stats()
    assert m.query_node(('le', 'petit')) == m.query_node(('le', 'gros'))



