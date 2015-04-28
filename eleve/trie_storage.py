from eleve.storage import Storage

#RMQ: Peut etre cela peut etre direct dans storage.py pour ne pas multiplié les .py
# ca reste une implémenation abstract de Storage (un peu moins que Storage)
class TrieStorage(Storage):
    """ Abstract :class:`.Storage` that use two trees (for forward and backward)
    """
    trie_class = None

    def __init__(self, path):
        self.fwd_trie = self.trie_class(path and (path + ".fwd"))
        self.bwd_trie = self.trie_class(path and (path + ".bwd"))

    def add_ngram(self, ngram, *args, **kwargs):
        self.fwd_trie.add_ngram(ngram, *args, **kwargs)
        self.bwd_trie.add_ngram(ngram[::-1], *args, **kwargs)
    
    def query_autonomy(self, ngram, *args, **kwargs):
        result_fwd = self.query(ngram, *args, **kwargs)
        result_bwd = self.query(ngram[::-1], *args, **kwargs)
        return (result_fwd + result_bwd) / 2.

    def save(self, path):
        self.fwd_trie.save(path + ".fwd")
        self.bwd_trie.save(path + ".bwd")
