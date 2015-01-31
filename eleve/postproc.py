# -*- coding:utf8 -*-
import re

import eleve.nlptypes as NLP

re_timedate = re.compile(ur"([年月日號号時时點点鍾种分秒午]|早上|晚上|凌晨)")
re_adresses = re.compile(ur"([省縣县鄉乡部市村區区街路段巷弄]|大道)")



def PKU(words):
    result = []
    for w in words:
        if w.pos == "DATETIME":
            forms = re_timedate.sub("\\1 ", w.form).strip().split(" ")
            for f in forms:
                result.append(NLP.Wordform(f, w.pos, list(f)))
        elif w.pos == "ADDR":
            forms = re_adresses.sub("\\1 ", w.form).strip().split(" ")
            for f in forms:
                result.append(NLP.Wordform(f, w.pos, list(f)))
        else:
            result.append(w)
    return result



