from reliure_nlp.tokenisation.fr import tokeniser_fr
from nltk.corpus import reuters

from eleve import Eleve
from eleve.memory import MemoryStorage
from eleve.neo4j import Neo4jStorage
from eleve.merge import MergeStorage

def benchmark(storage_class, create=True):
    m = Eleve(3, 'test', storage_class)
    if create:
        m.clear()

    corpus = reuters.raw()

    tokens = list(filter(lambda t: t.category == '', tokeniser_fr(corpus)))[:10000]
    
    if create:
        m.add_sentence(tokens, 1)

    for i in range(1,5000,30):
        print(m.segment(tokens[i:i+30]))

if __name__ == '__main__':
    benchmark(MergeStorage)
