#!/usr/bin/python
from eleve_trie import Trie
from eleve.memory import MemoryStorage
import random
random.seed('palkeo')

t = Trie()
t2 = MemoryStorage(4)

for docid in range(1000):
    for ngram in range(4000):
        n = [int(random.expovariate(1e-2)) for _ in range(4)]
        t2.add_ngram(n, docid, 1)
