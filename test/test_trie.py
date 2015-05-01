import random

from eleve.storage.memory import MemoryTrie
from eleve.storage.incremental_memory import IncrementalMemoryTrie

def generate_random_ngrams():
    depth = random.randint(2,5)
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

def test_trie_class(trie_class, reference_class=MemoryTrie):
    depth, ngrams = generate_random_ngrams()
    test_trie = trie_class(depth)
    ref_trie = reference_class(depth)
    for n in ngrams:
        test_trie.add_ngram(n)
        ref_trie.add_ngram(n)
    test_trie.update_stats()
    ref_trie.update_stats()
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

def test_basic_trie(trie_class):
    m = trie_class(3)
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

if __name__ == '__main__':
    test_basic_trie(MemoryTrie)
    test_basic_trie(IncrementalMemoryTrie)
    test_trie_class(IncrementalMemoryTrie)
