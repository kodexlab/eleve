from typing import List
import unicodedata as ud

from eleve import Segmenter

def normalize(s: str) -> str:
    return ud.normalize("NFC", s)


def tokenize_by_unicode_category(s: str) -> List[str]:
    buf = []
    prev_cat = None
    for c in s:
        cat = ud.category(c)
        if cat == "Ll" or cat == "Lu":
            cat = "latin"
        if cat == prev_cat:
            buf[-1] = buf[-1] + c
        else:
            buf.append(c)
            prev_cat = cat
    return buf

def filter_cjk(toks: List[str]) -> List[str]:
    for tok in toks:
        try:
            if ud.name(tok[0]).startswith("CJK"):
                yield tok
            else:
                pass
        except:
            pass

def add_bies(s: str) -> str:
    if len(s) == 1:
        return s + "-S"
    else:
        bies = [s[0] + "-B"]
        for i in s[1:-1]:
            bies.append(i + "-I")
        bies.append(s[-1] + "-E")
        return " ".join(bies)


def segment_with_preprocessing(seg: Segmenter, sent:str) -> str:
    tokens = []
    for group in tokenize_by_unicode_category(sent):
        try:
            if ud.name(group[0]).startswith("CJK"):
                tokens.append(seg.segmentSentenceBIES(" ".join(group)))
            else:
                tokens.append(add_bies(group))
        except:
            tokens.append(add_bies(group))
    return " ".join(tokens)