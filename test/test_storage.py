import pytest

from eleve.storage import Storage
from eleve.cstorages import MemoryStorage as CMemoryStorage

@pytest.mark.parametrize("storage_class", [Storage, CMemoryStorage])
def test_basic_entropy(storage_class):
    """
    Forward that begins by « le petit »:
     - le petit chat
     - le petit chien
     - le petit None * 2
    Backward that begins by « petit le » :
     - petit le None * 2
     - petit le pour * 2
    --> count is the mean of 4 and 4, and entropy is the mean of 2 (the None are counted separately) and 1.5.
    """
    m = storage_class(2)

    m.add_sentence(['le','petit','chat'])
    m.add_sentence(['le','petit','chien'])
    m.add_sentence(['pour','le','petit'], 2)
    assert m.query_count(['le', 'petit']) == 4.0
    assert m.query_entropy(['le', 'petit']) == 1.75

