from reliure_nlp.tokenisation.fr import tokeniser_fr
from nltk.corpus import reuters

from eleve import Segmenter, MemoryStorage, LeveldbStorage


def benchmark(storage_class, create=True):
    m = storage_class(4)
    s = Segmenter(m, 3)
    if create:
        m.clear()

    corpus = reuters.raw()

    tokens = list(filter(lambda t: t.category == "", tokeniser_fr(corpus)))[:10000]

    if create:
        m.add_sentence(tokens)

    for i in range(1, 5000, 30):
        print(s.segment(tokens[i : i + 30]))


if __name__ == "__main__":
    import pstats, cProfile
    import pyximport

    pyximport.install()
    cProfile.runctx("benchmark(MemoryStorage)", globals(), locals(), "profile.prof")
    s = pstats.Stats("profile.prof")
    s.strip_dirs().sort_stats("time").print_stats()
