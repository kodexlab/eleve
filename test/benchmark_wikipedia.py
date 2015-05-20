from mw.xml_dump import Iterator
import bz2
import regex as re
import datetime
from eleve import Eleve
import random
import logging

#logging.getLogger().setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO)
logging.getLogger('py2neo').setLevel(logging.WARNING)

def main():
    dump = Iterator.from_file(bz2.open('/mnt/documents/Divers/frwiki-20150331-pages-articles.xml.bz2')) 

    RE_WORD = re.compile(r"[\w-]{1,30}", re.IGNORECASE)

    l = Eleve(2, 'wikipedia').clear()

    i = 0
    start = datetime.datetime.now()
    sentences = None
    for page in dump:
        i += 1
        print(i)
        if i % 10000 == 0:
            print('%s articles made. %s by second.' % (i, i // (datetime.datetime.now() - start).total_seconds()))

            random.shuffle(sentence)
            for sentence in sentences[:20]:
                print(sentence)
                print(l.segment(sentence))
                print()

        text = str(next(iter(page)).text).lower()

        sentences = text.split('.')
        sentences = list(filter(None, map(lambda p: RE_WORD.findall(p), sentences)))
        for sentence in sentences:
            l.add_sentence(sentence, i)

if __name__ == '__main__':
    main()
