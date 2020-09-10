from typing import List
import unicodedata as ud

from eleve import Segmenter
from functools import lru_cache

def normalize(s: str) -> str:
    return ud.normalize("NFC", s)

@lru_cache(maxsize=10000)
def getCategory(c: str) -> str:
    cat = ud.category(c)
    if cat == "Ll" or cat == "Lu":
        cat = "latin"
    return cat

@lru_cache(maxsize=10000)
def isCJK(tok: str) -> bool:
    try:
        return ud.name(tok[0]).startswith("CJK")
    except:
        return False


def tokenize_by_unicode_category(s: str) -> List[str]:
    buf = []
    prev_cat = None
    for c in s:
        cat = getCategory(c)
        if cat == prev_cat:
            buf[-1] = buf[-1] + c
        else:
            buf.append(c)
            prev_cat = cat
    return buf

def filter_cjk(toks: List[str]) -> List[str]:
    for tok in toks:
        if isCJK(tok):
            yield tok
        else:
            pass

def add_bies(s: str) -> List[str]:
    if len(s) == 1:
        return [s + "-S"]
    else:
        bies = [s[0] + "-B"]
        for i in s[1:-1]:
            bies.append(i + "-I")
        bies.append(s[-1] + "-E")
        return bies

def segment_with_preprocessing(seg: Segmenter, sent:str) -> str:
    tokens = []
    for group in tokenize_by_unicode_category(sent):
        try:
            if isCJK(group[0]):
                words = ["".join(w) for w in seg.segment(list(group))]
                for w in words:
                    tokens.extend(add_bies(w))
            else:
                tokens.extend(add_bies(group))
        except:
            tokens.extend(add_bies(group))
    return " ".join(tokens)

