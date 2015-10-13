import pytest

from eleve import Segmenter

from test_storage import \
    PyMemoryStorage, CMemoryStorage, PyLeveldbStorage, CLeveldbStorage

from reliure_nlp.tokenisation.zh import engine_basic

@pytest.mark.parametrize("storage_class", [PyMemoryStorage, PyLeveldbStorage, CMemoryStorage, CLeveldbStorage])
def test_basic_segmentation(storage_class):
    l = storage_class(3)
    l.clear()
    m = Segmenter(l, 2)
    l.add_sentence(['je', 'vous', 'parle', 'de', 'hot', 'dog'], 1)
    l.add_sentence(['j', 'ador', 'les', 'hot', 'dog'], 1)
    l.add_sentence(['hot', 'dog', 'ou', 'pas'], 1)
    l.add_sentence(['hot', 'dog', 'ou', 'sandwich'], 1)

    assert m.segment(['je', 'deteste', 'les', 'hot', 'dog']) == [['je'], ['deteste'], ['les'], ['hot', 'dog']]

"""
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
