import datetime

from test_trie import generate_random_ngrams

from eleve.memory import MemoryTrie
from eleve.leveldb import LeveldbTrie
from eleve.c_leveldb.cleveldb import LeveldbTrie as CLeveldbTrie
from eleve.c_memory.cmemory import MemoryTrie as CMemoryTrie

import random

random.seed("palkeo")


def benchmark_trie_class(trie_class, reference_class=CMemoryTrie):
    ngrams = generate_random_ngrams()
    print("{} ngrams.".format(len(ngrams)))
    test_trie = trie_class("/tmp/test_trie")
    test_trie.clear()
    ref_trie = reference_class(5)

    t = datetime.datetime.now()
    for n in ngrams:
        ref_trie.add_ngram(n)
    time_construct_ref = datetime.datetime.now() - t
    print("Time to construct reference : {}".format(time_construct_ref))

    t = datetime.datetime.now()
    ref_trie.update_stats()
    time_update_ref = datetime.datetime.now() - t
    print("Time to update reference : {}".format(time_update_ref))

    t = datetime.datetime.now()
    for n in ngrams:
        ref_trie.query_autonomy(n)
    time_query_ref = datetime.datetime.now() - t
    print("Time to query reference : {}".format(time_query_ref))

    t = datetime.datetime.now()
    for n in ngrams:
        test_trie.add_ngram(n)
    time_construct_test = datetime.datetime.now() - t
    print("Time to construct test : {}".format(time_construct_test))

    t = datetime.datetime.now()
    test_trie.update_stats()
    time_update_test = datetime.datetime.now() - t
    print("Time to update test : {}".format(time_update_test))

    t = datetime.datetime.now()
    for n in ngrams:
        test_trie.query_autonomy(n)
    time_query_test = datetime.datetime.now() - t
    print("Time to query test : {}".format(time_query_test))


if __name__ == "__main__":
    import pstats, cProfile
    import pyximport

    pyximport.install()
    cProfile.runctx(
        "benchmark_trie_class(CLeveldbTrie)", globals(), locals(), "profile.prof"
    )
    s = pstats.Stats("profile.prof")
    s.strip_dirs().sort_stats("time").print_stats()
