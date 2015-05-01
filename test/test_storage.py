import pytest

from eleve.storage.incremental_memory import IncrementalMemoryStorage
from eleve.storage.memory import MemoryStorage

@pytest.mark.parametrize("storage_class", [MemoryStorage, IncrementalMemoryStorage])
def test_basic_storage(storage_class):
    m = storage_class(3)
    m.add_ngram(('le','petit','chat'))
    m.add_ngram(('le','petit','chien'))
    m.add_ngram(('pour','le','petit'), freq=2)
    m.update_stats()
    assert m.query_node(('le', 'petit')) == (2.0, 0.5)
