from typing import List
from pathlib import Path
from eleve.memory import MemoryStorage as Storage, CSVStorage
from eleve.preprocessing import chinese
from eleve import Segmenter


CORPUS = Path('/home/pierre/Corpora/PKU/all.raw.u8')


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

def train(corpus) -> Storage:
    storage = Storage(6)
    for l in open(corpus):
        for chunk in preproc(l):
            storage.add_sentence(chunk)
    return storage

#print(storage.get_voc())

if __name__ == "__main__":
    storage = train(CORPUS)
    for i in range(1):
        print(i)
        #segment_file(storage, CORPUS, Path(f"/tmp/text-{i}.txt"), bies=False)
        storage.prune(50)
        CSVStorage.writeCSV(storage, storage.get_voc(),f"/tmp/lex-{i}.csv", ' ')
