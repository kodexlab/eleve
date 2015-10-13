import pytest
import re
import tempfile
import shutil

from eleve import PyMemoryStorage, PyLeveldbStorage as BPyLeveldbStorage, CMemoryStorage, CLeveldbStorage as BCLeveldbStorage
from test_trie import compare_node

class StorageWithPath:
    def __init__(self, order):
        self.fs_path = tempfile.mkdtemp()
        super().__init__(order, self.fs_path)

    def __del__(self):
        shutil.rmtree(self.fs_path)

class PyLeveldbStorage(StorageWithPath, BPyLeveldbStorage):
    pass

class CLeveldbStorage(StorageWithPath, BCLeveldbStorage):
    pass


@pytest.mark.parametrize("storage_class", [PyMemoryStorage, CMemoryStorage, PyLeveldbStorage, CLeveldbStorage])
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
    m = storage_class(3)
    m.clear()

    m.add_sentence(['le','petit','chat'])
    m.add_sentence(['le','petit','chien'])
    m.add_sentence(['pour','le','petit'], 2)
    assert m.query_count(['le', 'petit']) == 4.0
    assert m.query_entropy(['le', 'petit']) == 1.75

@pytest.mark.parametrize("storage_class", [CMemoryStorage, PyLeveldbStorage, CLeveldbStorage])
def test_storage(storage_class, ref_class=PyMemoryStorage):
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
