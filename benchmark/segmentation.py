import re

from eleve import Eleve

RE_WORD = re.compile(r"\w+", re.IGNORECASE)


def test_basic_segmentation():
    l = Eleve(5)

    doc = open("fixtures/btree.txt").read()
    sentences = doc.split(".")
    sentences = list(filter(None, map(lambda p: RE_WORD.findall(p), sentences)))

    for sentence in sentences:
        l.add_sentence(sentence)

    for sentence in sentences:
        print(sentence)
        print(l.segment(sentence))
        print()


if __name__ == "__main__":
    test_basic_segmentation()
