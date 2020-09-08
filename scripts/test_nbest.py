from eleve import CMemoryStorage as Storage
from eleve import Segmenter

import sys

corpus_file = sys.argv[1]

with open(corpus_file) as f:
    storage = Storage(10)
    corpus = []
    for line in f:
        tokens = list(line.strip().replace(" ", ""))
        storage.add_sentence(tokens)
        corpus.append(tokens)
    seg = Segmenter(storage)
    for tokens in corpus:
        result = seg.segment_nbest(tokens, 5)
        for ibest in result:
            print("  ".join(["".join(w) for w in ibest]))
