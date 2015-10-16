import pytest
from eleve import Segmenter

from conftest import all_storage_nocreate

@pytest.mark.parametrize("storage", all_storage_nocreate, indirect=True)
def test_basic_segmentation(storage):
    ngram_length = 3
    segmenter = Segmenter(storage, 2)
    storage.add_sentence(['je', 'vous', 'parle', 'de', 'hot', 'dog'], ngram_length=ngram_length)
    storage.add_sentence(['j', 'ador', 'les', 'hot', 'dog'], ngram_length=ngram_length)
    storage.add_sentence(['hot', 'dog', 'ou', 'pas'], ngram_length=ngram_length)
    storage.add_sentence(['hot', 'dog', 'ou', 'sandwich'], ngram_length=ngram_length)

    assert segmenter.segment(['je', 'deteste', 'les', 'hot', 'dog']) == [['je'], ['deteste'], ['les'], ['hot', 'dog']]
    assert segmenter.segment(['un', 'chat', 'noir', 'et', 'blanc']) == [['un'], ['chat'], ['noir'], ['et'], ['blanc']]

"""
from reliure_nlp.tokenisation.zh import engine_basic

@pytest.mark.parametrize("storage_class", [CMemoryStorage, PyLeveldbStorage, CLeveldbStorage])
def test_zh_segmentation(storage_class, ref_class=PyMemoryStorage):
    test = storage_class(7)
    ref = ref_class(7)
    test.clear()
    ref.clear()

    unsegmented = []
    training = open("fixtures/pku_test.utf8").read().replace(' ', '')
    tokens = engine_basic(training)
    for token in tokens:
        if token.category == 'unsegmented':
            unsegmented.append(list(token.form))

    for u in unsegmented:
        test.add_sentence(u)
        ref.add_sentence(u)

    segmenter_test = Segmenter(test, 6)
    segmenter_ref = Segmenter(ref, 6)

    for u in unsegmented:
        assert segmenter_test.segment(u) == segmenter_ref.segment(u)
"""
