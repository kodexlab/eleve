import pytest
import re
import gc

from eleve.storage import MemoryStorage, LevelStorage
from eleve.cstorages import MemoryStorage as CMemoryStorage

from test_trie import compare_node

@pytest.mark.parametrize("storage_class", [MemoryStorage, CMemoryStorage, LevelStorage])
def test_basic_entropy(storage_class):
    """
    Forward that begins by « le petit »:
     - le petit chat
     - le petit chien
     - le petit $ * 2
    Backward that begins by « petit le » :
     - petit le ^ * 2
     - petit le pour * 2
    --> count is the mean of 4 and 4, and entropy is the mean of 2 (the None are counted separately) and 1.5.
    """
    gc.collect()
    m = storage_class(3)
    m.clear()

    m.add_sentence(['le','petit','chat'])
    m.add_sentence(['le','petit','chien'])
    m.add_sentence(['pour','le','petit'], 2)
    assert m.query_count(['le', 'petit']) == 4.0
    assert m.query_entropy(['le', 'petit']) == 1.75

@pytest.mark.parametrize("storage_class", [CMemoryStorage, LevelStorage])
def test_storage(storage_class, ref_class=MemoryStorage):
    gc.collect()
    test = storage_class(4)
    ref = ref_class(4)
    test.clear()
    ref.clear()

    sentences = [re.findall(r'\w+', sentence) for sentence in open('fixtures/btree.txt').read().split('\n')]
    for sentence in sentences:
        test.add_sentence(sentence)
        ref.add_sentence(sentence)

    for sentence in sentences:
        for start in range(len(sentence)):
            for i in range(6):
                ngram = sentence[start:start+i]
                compare_node(ngram, ref, test)
