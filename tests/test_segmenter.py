import pytest
from eleve import Segmenter

from conftest import parametrize_storage


@parametrize_storage(default_ngram_length=3)
def test_segmentation_basic(storage):
    storage.add_sentence("je vous parle de hot dog".split())
    storage.add_sentence("j ador les hot dog".split())
    storage.add_sentence("hot dog ou pas".split())
    storage.add_sentence("hot dog ou sandwich".split())

    segmenter = Segmenter(storage)
    assert segmenter.segment("je deteste les hot dog".split()) == [
        ["je"],
        ["deteste"],
        ["les"],
        ["hot", "dog"],
    ]
    assert segmenter.segment("un chat noir et blanc".split()) == [
        ["un"],
        ["chat"],
        ["noir"],
        ["et"],
        ["blanc"],
    ]


@parametrize_storage(default_ngram_length=2)
def test_segmentation_2grams(storage):
    storage.add_sentence("je vous parle de hot dog".split())
    storage.add_sentence("j ador les hot dog".split())
    storage.add_sentence("hot dog ou pas".split())
    storage.add_sentence("hot dog ou sandwich".split())

    segmenter = Segmenter(storage)
    assert segmenter.segment("je deteste les hot dog".split()) == [
        ["je"],
        ["deteste"],
        ["les"],
        ["hot"],
        ["dog"],
    ]


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
