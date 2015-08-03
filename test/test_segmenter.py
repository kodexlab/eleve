import pytest

from eleve.storage import Storage
from eleve.cstorages import MemoryStorage as CMemoryStorage
from eleve.segment import Segmenter

@pytest.mark.parametrize("storage_class", [Storage, CMemoryStorage])
def test_basic_segmentation(storage_class):
    l = storage_class(3)
    m = Segmenter(l, 2)
    l.add_sentence(['je', 'vous', 'parle', 'de', 'hot', 'dog'], 1)
    l.add_sentence(['j', 'ador', 'les', 'hot', 'dog'], 1)
    l.add_sentence(['hot', 'dog', 'ou', 'pas'], 1)
    l.add_sentence(['hot', 'dog', 'ou', 'sandwich'], 1)

    assert m.segment(['je', 'deteste', 'les', 'hot', 'dog']) == [['je'], ['deteste'], ['les'], ['hot', 'dog']]
