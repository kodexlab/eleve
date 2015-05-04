import pytest

from eleve.storage.incremental_memory import IncrementalMemoryStorage
from eleve.storage.memory import MemoryStorage

@pytest.mark.parametrize("storage_class", [MemoryStorage, IncrementalMemoryStorage])
def test_basic_storage(storage_class):
    """
    Forward that begins by « le petit »:
     - le petit chat
     - le petit chien
     - le petit None * 2
    Backward that begins by « petit le » :
     - petit le None * 2
     - petit le pour * 2
    --> count is the mean of 4 and 4, and entropy is the mean of 1.5 and 1.
    """
    m = storage_class(3)
    m.add_sentence(['le','petit','chat'])
    m.add_sentence(['le','petit','chien'])
    m.add_sentence(['pour','le','petit'], freq=2)
    assert m.query_node(('le', 'petit')) == (4.0, 1.25)
