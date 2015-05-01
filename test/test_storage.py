from eleve.storage.incremental_memory import IncrementalMemoryStorage
from eleve.storage.memory import MemoryStorage

from test_trie import test_trie_class

def test_basic_storage(storage_class):
    m = storage_class(3)
    m.add_ngram(('le','petit','chat'))
    m.add_ngram(('le','petit','chien'))
    m.add_ngram(('pour','le','petit'), freq=2)
    m.update_stats()
    assert m.query_node(('le', 'petit')) == (2.0, 0.5)

if __name__ == '__main__':
    test_basic_storage(MemoryStorage)
    test_basic_storage(IncrementalMemoryStorage)
    # TODO: Won't work...
    #test_trie_class(IncrementalMemoryStorage, reference_class=MemoryStorage)
