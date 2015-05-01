import random
import datetime

from eleve.storage.memory import MemoryTrie
from eleve.storage.trivial import TrivialTrie

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

def test_trie_class(trie_class):
    depth, ngrams = generate_random_ngrams()
    test_trie = trie_class(depth)
    ref_trie = TrivialTrie(depth)
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

def benchmark_trie_class(trie_class):
    depth, ngrams = generate_random_ngrams()
    print('{} ngrams.'.format(len(ngrams)))
    test_trie = trie_class(depth)
    ref_trie = TrivialTrie(depth)

    t = datetime.datetime.now()
    for n in ngrams:
        ref_trie.add_ngram(n)
    time_construct_ref = datetime.datetime.now() - t
    print('Time to construct reference : {}'.format(time_construct_ref))

    t = datetime.datetime.now()
    ref_trie.update_stats()
    time_update_ref = datetime.datetime.now() - t
    print('Time to update reference : {}'.format(time_update_ref))

    t = datetime.datetime.now()
    for n in ngrams:
        ref_trie.query_autonomy(n)
    time_query_ref = datetime.datetime.now() - t
    print('Time to query reference : {}'.format(time_query_ref))

    t = datetime.datetime.now()
    for n in ngrams:
        test_trie.add_ngram(n)
    time_construct_test = datetime.datetime.now() - t
    print('Time to construct test : {}'.format(time_construct_test))

    t = datetime.datetime.now()
    test_trie.update_stats()
    time_update_test = datetime.datetime.now() - t
    print('Time to update test : {}'.format(time_update_test))

    t = datetime.datetime.now()
    for n in ngrams:
        test_trie.query_autonomy(n)
    time_query_test = datetime.datetime.now() - t
    print('Time to query test : {}'.format(time_query_test))

if __name__ == '__main__':
    test_trie_class(MemoryTrie)
    benchmark_trie_class(MemoryTrie)
