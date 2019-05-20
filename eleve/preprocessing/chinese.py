from typing import List
import unicodedata as ud


def normalize(s: str) -> str:
    return ud.normalize("NFC", s)


def tokenize_by_unicode_category(s: str) -> List[str]:
    buf = []
    prev_cat = None
    for c in s:
        cat = ud.category(c)
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
