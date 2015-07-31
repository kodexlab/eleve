from eleve.memory import MemoryTrie

# -*- coding:utf8 -*-
""" Storage interface for LM
"""

class Storage:
    order = None

    def __init__(self, order, path, trie_class=MemoryTrie, *args, **kwargs):
        assert order > 1
        assert isinstance(path, str)
        self.order = order

        self.bwd = trie_class(order + 1, path + '_bwd', *args, **kwargs)
        self.fwd = trie_class(order + 1, path + '_fwd', *args, **kwargs)

    def add_sentence(self, sentence, freq=1):
        token_list = ['^'] + sentence + ['$']
        for i in range(len(token_list) - 1):
            self.fwd.add_ngram(token_list[i:i+self.order+1], freq)
        token_list = token_list[::-1]
        for i in range(len(token_list) - 1):
            self.bwd.add_ngram(token_list[i:i+self.order+1], freq)

    def clear(self):
        self.bwd.clear()
        self.fwd.clear()

    def query_autonomy(self, ngram):
        result_fwd = self.fwd.query_autonomy(ngram)
        result_bwd = self.bwd.query_autonomy(ngram[::-1])
        if result_fwd is None or result_bwd is None:
            return None
        return (result_fwd + result_bwd) / 2
     
    def query_ev(self, ngram):
        result_fwd = self.fwd.query_ev(ngram)
        result_bwd = self.bwd.query_ev(ngram[::-1])
        if result_fwd is None or result_bwd is None:
            return None
        return (result_fwd + result_bwd) / 2

    def query_count(self, ngram):
        count_fwd = self.fwd.query_count(ngram)
        count_bwd = self.bwd.query_count(ngram[::-1])
        return (count_fwd + count_bwd) / 2

    def query_entropy(self, ngram):
        entropy_fwd = self.fwd.query_entropy(ngram)
        entropy_bwd = self.bwd.query_entropy(ngram[::-1])
        if entropy_fwd is None or entropy_bwd is None:
            return None
        return (entropy_fwd + entropy_bwd) / 2
