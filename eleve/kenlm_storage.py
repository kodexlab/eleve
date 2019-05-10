import kenlm
from typing import List, Tuple, Set, Sequence
from multiprocessing import Pool
from collections import defaultdict
from functools import reduce, lru_cache

import numpy as np

class KenLMStorage:
    def __init__(self, arpa_fw: str, mmap_fw : str, mmap_bw: str, ngram_length: int=5):
        self.arpa = arpa_fw
        self.fw = kenlm.LanguageModel(mmap_fw)
        self.bw = kenlm.LanguageModel(mmap_bw)
        self.default_ngram_length = ngram_length
        self.data_fw = []
        self.data_bw = []
        self.voc = []
        for i in range(ngram_length+1):
            self.data_fw.append(defaultdict(dict))
            self.data_bw.append(defaultdict(dict))
            self.voc.append([])
        self.norm_fw = [(0.0, 1.0)] * ngram_length
        self.norm_bw = [(0.0,1.0)] * ngram_length
        print("loading vocab")
        self._load_vocab()
        print("computing nvbe")
        self._computeNVBE()


    def _load_vocab(self):
        self.voc[0].append(())
        with open(self.arpa) as f:
            n = -1
            for l in f:
                l = l[:-1] # strip \n
                if l.startswith("\\"):
                    n += 1
                elif l == "":
                    pass
                elif n > 0:
                    fields = l.split("\t")
                    ng = tuple(fields[1].split(" "))
                    if "<s>" in ng or "</s>" in ng:
                        pass
                    else:
                        self.voc[n].append(ng)

    def _computeNVBE(self):
        # get ngrams proba
        for (i, ngrams) in enumerate(self.voc):
            if i > 0:
                for ng in ngrams:
                    # forward
                    base = ng[:-1]
                    last = ng[-1:]
                    p = 10 ** self.fw.score(" ".join(ng), bos=False, eos=False)
                    self.data_fw[i-1][base][last] = p
                    # backward
                    ng = ng[::-1]
                    base = ng[:-1]
                    last = ng[-1:]
                    p = 10 ** self.bw.score(" ".join(ng), bos=False, eos=False)
                    self.data_bw[i - 1][base][last] = p
        # compute entropies
        for i, probas in enumerate(self.data_fw):
            for ng, nexts in probas.items():
                self.data_fw[i][ng] = self._entropy(nexts.values())
        for i, probas in enumerate(self.data_bw):
            for ng, nexts in probas.items():
                self.data_bw[i][ng] = self._entropy(nexts.values())
        # compute vbe
        for i in range(len(self.data_fw)-1, 0, -1):
            for ng,h in self.data_fw[i].items():
                prev = ng[:-1]
                prevH = self.data_fw[i -1][prev]
                self.data_fw[i][ng] = h - prevH
        for i in range(len(self.data_bw)-1, 0, -1):
            for ng,h in self.data_bw[i].items():
                prev = ng[:-1]
                prevH = self.data_bw[i -1][prev]
                self.data_bw[i][ng] = h - prevH


    def normalize(self):
        # compute normalization parameters
        self.norm_fw = []
        for data in self.data_fw[:-1]:
            values = np.array(list(data.values()))
            mean = values.mean()
            std = values.std()
            self.norm_fw.append((mean, std))
        self.norm_bw = []
        for data in self.data_bw[:-1]:
            values = np.array(list(data.values()))
            mean = values.mean()
            std = values.std()
            self.norm_bw.append((mean, std))


    def _entropy(self, values: Sequence[float]) -> float:
        return -sum([p * np.log(p) for p in values])

    def query_autonomy(self, s: Sequence[str]) -> float:
        l = len(s)
        t = tuple(s)
        m,d = self.norm_fw[l-1]
        if not t in self.data_fw[l]:
            return float('nan')
        else:
            fw = (self.data_fw[l][t] - m)
            m, d = self.norm_bw[l-1]
            t = t[::-1]
            if not t in self.data_bw[l]:
                return float('nan')
            else:
                return fw + (self.data_bw[l][t] - m)
