from collections import namedtuple


SyntacticLink = namedtuple("SyntacticLink", "idx rel")

class Token(object):
    __slots__ = ("seq", "idx", "form", "category", "_meta")

    def __init__(self, form, category="", idx=None, seq=None, meta=None):
        self.seq = seq
        self.idx = idx
        self.form = form
        self.category = category
        self._meta = meta
    
    @property
    def meta(self):
        return self._meta if self._meta is not None else {}

    def next(self):
        return self.seq[self.idx+1] #TODO: add idx check and seq is not None

class Wordform(object):
    __slots__ = ("seq", "idx", "form", "pos", "tokens", "_meta", )

    def __init__(self, wordform, pos, tokens=None, idx=None, seq=None, meta=None):
        self.form = wordform
        self.tokens = tokens if tokens else [wordform]
        self.pos = pos
        self.idx = idx
        self.seq = seq
        self._meta = meta
    
    @property
    def meta(self):
        return self._meta if self._meta is not None else {}


class DepNode(Wordform):
    __slots__ = ("tree", "lemma", "morpho", "governor")

    def __init__(self, wordform, pos, lemma, morpho, governor, relation, idx=None, seq=None, meta=None):
        super(DepNode, self).__init__(wordform, pos, idx, seq, meta)
        self.lemma = lemma
        self.morpho = morpho
        self.governor = SyntacticLink(governor, relation)


class DeepNode(DepNode):
    __slots__ = ("deep_governors",)

    def __init__(self, wordform, pos, lemma, morpho, governor, relation, deep_governors=None, idx=None, seq=None, meta=None):
        super(DeepNode, self).__init__(wordform, pos, idx, seq, meta)
        self.deep_governors = deep_governors if deep_governors else []


class TokenSequence(object):
    __slots__ = ("sequence", "_meta")

    def __init__(self, sequence, meta=None):
        self.sequence = sequence
        self._meta = meta

    @property
    def meta(self):
        return self._meta if self._meta else {}

class WordformSequence(TokenSequence):

    def __init__(self, sequence, meta=None):
        super(WordformSequence, self).__init__(sequence, meta)

class SyntaxTree(WordformSequence):
    __slots__ = ("_children",)

    def __init__(self, sequence, meta=None):
        super(SyntaxTree, self).__init__(sequence, meta)
        self._children = None #TODO: pre-calcul


class DeepSyntaxGraph(SyntaxTree):

    def __init__(self, sequence, meta):
        super(DeepSyntaxGraph, self).__init__(sequence, meta)
