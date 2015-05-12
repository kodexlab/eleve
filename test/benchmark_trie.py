import datetime

from test_storage import generate_random_ngrams
from eleve.memory import MemoryStorage
from eleve.neo4j import Neo4jStorage

def benchmark_trie_class(trie_class, reference_class=MemoryStorage):
    depth, ngrams = generate_random_ngrams()
    print('{} ngrams.'.format(len(ngrams)))
    test_trie = trie_class(depth)
    ref_trie = reference_class(depth)

    t = datetime.datetime.now()
    for n in ngrams:
        ref_trie.add_ngram(n, 1)
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
        test_trie.add_ngram(n, 1)
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
    benchmark_trie_class(Neo4jStorage)
