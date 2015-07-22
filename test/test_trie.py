import pytest
import random
import tempfile
import os

from eleve.memory import MemoryTrie

def float_equal(a, b):
    return (a is None and b is None) or abs(a - b) < 1e-6

def generate_random_ngrams():
    """ Generate list of random n-grams (of int)
    """
    depth = random.randint(2,3)
    m = []

    def add(prefix):
        for i in range(int(random.expovariate(0.2) + 1)):
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
    
    ngrams = set(map(lambda ngram_count: tuple(ngram_count[0]), ref_trie))
    for i, n in enumerate(set(ngrams)):
        if i > 20:
            break
        ngrams.add(tuple(n[:-1] + ('nonexistent',)))
        ngrams.add(tuple(n[:-2] + ('nonexistent',)))
        ngrams.add(tuple(n[:-2] + ('nonexistent','nonexistent')))
    ngrams.add(None)

    for ngram in ngrams:
        count_ref, entropy_ref = ref_trie.query_count(ngram), ref_trie.query_entropy(ngram)
        count_test, entropy_test = test_trie.query_count(ngram), test_trie.query_entropy(ngram)
        assert count_ref == count_test
        assert float_equal(entropy_ref, entropy_test)

        ev_ref = ref_trie.query_ev(ngram)
        ev_test = test_trie.query_ev(ngram)
        assert float_equal(ev_ref, ev_test)

        if ngram:
            autonomy_ref = ref_trie.query_autonomy(ngram, z_score=False)
            autonomy_test = test_trie.query_autonomy(ngram, z_score=False)
            assert float_equal(autonomy_ref, autonomy_test)

            try:
                autonomy_ref = ref_trie.query_autonomy(ngram, z_score=True)
                autonomy_test = test_trie.query_autonomy(ngram, z_score=True)
                assert float_equal(autonomy_ref, autonomy_test)
            except ZeroDivisionError:
                # in case the variance is null, because we are on the last level...
                with pytest.raises(ZeroDivisionError):
                    ref_trie.query_autonomy(ngram, z_score=True)
                with pytest.raises(ZeroDivisionError):
                    test_trie.query_autonomy(ngram, z_score=True)
        else:
            with pytest.raises(ValueError):
                ref_trie.query_autonomy(ngram)
            with pytest.raises(ValueError):
                test_trie.query_autonomy(ngram)

@pytest.mark.parametrize("trie_class", [])
def test_trie_class(trie_class, reference_class=MemoryTrie):
    """ Compare implementation against reference class (on random ngrams lists)
    """
    depth, ngrams = generate_random_ngrams()
    test_trie = trie_class(depth, 'test').clear()
    ref_trie = reference_class(depth, 'test').clear()
    for n in ngrams:
        test_trie.add_ngram(n)
        ref_trie.add_ngram(n)
    compare_tries(ref_trie, test_trie)

@pytest.mark.parametrize("trie_class", [MemoryTrie])
def test_save_load_trie(trie_class):
    """ Test save/load methods (on random ngrams lists)
    """
    depth, ngrams = generate_random_ngrams()
    test_trie = trie_class(depth)
    for n in ngrams:
        test_trie.add_ngram(n)
    # test load/save
    with tempfile.TemporaryDirectory(prefix='eleve_') as t:
        fn = os.path.join(t, 'test_trie')
        test_trie.save(fn)
        reloaded_trie = trie_class.load(fn)
    compare_tries(test_trie, reloaded_trie)

@pytest.mark.parametrize("trie_class", [MemoryTrie])
def test_basic_trie(trie_class):
    """ Minimal test on simple example
    """
    m = trie_class(3, 'test').clear()
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
