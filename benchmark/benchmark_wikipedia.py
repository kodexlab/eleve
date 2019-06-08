from mw.xml_dump import Iterator
import bz2
import regex as re
import datetime

from eleve import LeveldbStorage, MemoryStorage

import random


def main():
    dump = Iterator.from_file(
        bz2.open("/mnt/documents/Divers/frwiki-20150331-pages-articles.xml.bz2")
    )

    RE_WORD = re.compile(r"[\w-]{1,30}", re.IGNORECASE)

    l = LeveldbStorage(3)  # , path='/home/palkeo/Divers/stage_wikipedia')
    l.clear()

    i = 0
    wcount = 0
    start = datetime.datetime.now()
    sentences = None
    for page in dump:
        i += 1
        print(
            "Article %s, %s tokens, %s tokens/second"
            % (i, wcount, wcount // (datetime.datetime.now() - start).total_seconds())
        )

        text = str(next(iter(page)).text).lower()

        sentences = text.split(".")
        sentences = list(filter(None, map(lambda p: RE_WORD.findall(p), sentences)))
        for sentence in sentences:
            wcount += len(sentence)
            l.add_sentence(sentence)


if __name__ == "__main__":
    main()
