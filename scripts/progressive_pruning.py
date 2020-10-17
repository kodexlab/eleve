from typing import List
from pathlib import Path
from eleve.memory import MemoryStorage as Storage, CSVStorage
from eleve.preprocessing import chinese
from eleve import Segmenter


CORPUS = Path('/home/pierre/Corpora/PKU/small.raw.u8')


def preproc(l: str) -> List[str]:
    chunks = chinese.tokenize_by_unicode_category(l)
    return [cjk for cjk in chinese.filter_cjk(chunks)]



def segment_file(storage, input_file: Path, output_file: Path, bies:bool=True):
    segmenter = Segmenter(storage)
    with open(input_file) as f:
        with open(output_file, "w") as out:
            for line in f:
                line = line[:-1]
                if line.strip() != "":
                    out.write(chinese.segment_with_preprocessing(segmenter, line, bies) + "\n")


storage = Storage()
for l in open(CORPUS):
    for chunk in preproc(l):
        storage.add_sentence(chunk)

#print(storage.get_voc())


CSVStorage.writeCSV(storage, storage.get_voc(),"/tmp/test.csv", 'à')
storage2 = CSVStorage("/tmp/test.csv", "à")

segment_file(storage, CORPUS, Path("/tmp/out.txt"), bies=False)
segment_file(storage2, CORPUS, Path("/tmp/out2.txt"), bies=False)
