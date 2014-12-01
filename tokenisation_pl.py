# -*- coding:utf8 -*-
u""" tokenisation and token preprocessing module

>>> from pprint import pprint
>>> # the default tokeniser for zh
>>> pprint(list( engine_default([u"bu 好22", ]) ))
[[Token(form=[u'b', u'u'], category=u'WLATIN'),
  Token(form=[u' '], category=u'PUNCT'),
  Token(form=[u'\\u597d'], category=u'CJK'),
  Token(form=[u'2', u'2'], category=u'NUM')]]

>>> # the default one for fr, en, etc...
>>> pprint(list( engine_words_punct([u"Un chat noir !", "une sourie verte ?"]) ))
[[Token(form=[u'Un', u'chat', u'noir'], category='unsegmented'),
  Token(form=[u'!'], category=u'PUNCT')],
 [Token(form=[u'une', u'sourie', u'verte'], category='unsegmented'),
  Token(form=[u'?'], category=u'PUNCT')]]
>>> # it can also be called on a simple string:
>>> pprint(list( engine_words_punct.apply_on_string(u"Un chat noir !") ))
[Token(form=[u'Un', u'chat', u'noir'], category='unsegmented'),
 Token(form=[u'!'], category=u'PUNCT')]
"""

import re
from collections import namedtuple
import codecs

import unicodedata as ud

from cello.pipeline import Composable

from nlptypes import Token, Wordform, WordformSequence


# Token sequence processing modules
O_BOUNDARY = u"\ue000"    # separator between tokens
C_BOUNDARY = u"\ue001"    # separator between tokens
FCSEP = u"\ue002"       # separator between token form and token category
TOKSEP = u"\ue003"      # separator used inside a token form


UNIPUNCT = set(['SPACE',
                'SEMICOLON',
                'STOP',
                'MARK',
                'BRACKET',
                'COLON',
                'PARENTHESIS',
                'APOSTROPHE',
                'COMMA'])


# Basic Token object
def splitform(wordform):
    """ Token method that split it form
    """
    tokens = wordform.form.split(TOKSEP)
    wordform.form = "".join(tokens)
    wordform.tokens = tokens
    return wordform

####
## Initial tokenisers

class CharAsToken(Composable):
    """ Create a sequence of 'char-Token' from an string.
    A Token is created for each char.
    
    >>> tokenizer = CharAsToken()
    >>> list(tokenizer("ABC"))
    [Token(form='A', category=''), Token(form='B', category=''), Token(form='C', category='')]
    """
    def __init__(self):
        super(CharAsToken, self).__init__()

    def __call__(self, line):
        """
        :param line: unicode string
        :returns: a list of Token
        """
        return [Token(char) for char in line.strip()]

class WordAsToken(Composable):
    """ Create a sequence of 'word-Token' from an string.
    A Token is created for each word (space separted).
    
    >>> tokenizer = WordAsToken()
    >>> list(tokenizer("un chat , noir"))
    [Token(form='un', category='WTOKEN'), Token(form='chat', category='WTOKEN'), Token(form=',', category='WTOKEN'), Token(form='noir', category='WTOKEN')]
    """
    def __init__(self):
        super(WordAsToken, self).__init__()

    def __call__(self, line):
        """
        :param line: unicode string
        :returns: a list of Token
        """
        return [Token(word, "") for word in line.strip().split()]



class Module(Composable):
    u""" Process a Token list according to a pseudo regexp and a convertor function

    >>> charTagger = Module("(./.*)", TokenCategorizer)
    >>> TokenCategorizer([(u'1', u''), (u'H', u''), (u'2', u'')])
    [Token(form=u'1', category='DIGIT'), Token(form=u'H', category='LATIN'), Token(form=u'2', category='DIGIT')]
    >>> TokenCategorizer([(u'1', u''), (u'H', u'')])
    [Token(form=u'1', category='DIGIT'), Token(form=u'H', category='LATIN')]

    >>> filter = Module("([0-9]+/.*)", joinForms("NUM"))
    >>> filter([Token(form=u'17', category=u'WTOKEN'), Token(form=u'Hippies', category=u'WTOKEN')])
    [Token(form=u'17', category='NUM'), Token(form=u'Hippies', category=u'WTOKEN')]

    >>> filter = Module("(.*/WT)", joinForms("IS_OK"))
    >>> filter([(u'abc', u'WT'), (u'ef', u'WTOKEN')])
    [Token(form=u'abc', category='IS_OK'), Token(form=u'ef', category=u'WTOKEN')]

    >>> filter = Module(".*/WT", joinForms("IS_OK"))
    >>> filter([(u'abc', u'WT'), (u'ef', u'WTOKEN')])
    [Token(form=u'abc', category='IS_OK'), Token(form=u'ef', category=u'WTOKEN')]

    >>> filter = Module("[abc]*", joinForms("IS_OK"))
    >>> filter([(u'abc', u''), (u'aa', u'WTOKEN'), (u'ef', u'WTOKEN')])
    [Token(form=u'abc', category='IS_OK'), Token(form=u'aa', category='IS_OK'), Token(form=u'ef', category=u'WTOKEN')]

    >>> filter = Module("(ab)+", joinForms("IS_OK"))
    >>> filter([(u'ab', u'WTOKEN'), (u'ab', u'ABTOKEN'), (u'abab', u'WTOKEN'), (u'ab', u'WTOKEN')])
    [Token(form=u'ab\\ue003ab', category='IS_OK'), Token(form=u'abab', category=u'WTOKEN'), Token(form=u'ab', category='IS_OK')]

    >>> filter = Module("((ab)+/.*)", joinForms("IS_OK"))
    >>> filter([(u'ab', u'WTOKEN'), (u'ab', u''), (u'abab', u'WTOKEN'), (u'ab', u'WTOKEN')])
    [Token(form=u'ab', category='IS_OK'), Token(form=u'ab', category='IS_OK'), Token(form=u'abab', category='IS_OK'), Token(form=u'ab', category='IS_OK')]

    """
    def __init__(self, regexp, convertor):
        super(Module, self).__init__()
        #TODO attributes
        self.regexp = regexp
        self.convertor = convertor
        self.re = self._compile_re()

    def _compile_re(self):
        regex = []
        for tok in self.regexp.split():
            if tok == "|":
                regex.append(tok)
                continue
            left = ""
            right = ""
            while tok.startswith("("):
                left += "(?:"
                tok = tok[1:]
            if tok[-1] in "?+*" and (len(tok) >= 2 and tok[-2] == ")"):
                quantifier = tok[-1]
                tok = tok[:-1]
            else:
                quantifier = ""
            while tok.endswith(")"):
                right += tok[-1]
                tok = tok[:-1]
            if "/" in tok:
                forme, tag = tok.rsplit("/", 1)
            else:
                forme = tok
                tag = ".*"
            tok = FCSEP.join([forme,tag])  # set proper FCSEP
            tok = tok.replace(".", "[^%s%s%s]" % (C_BOUNDARY, O_BOUNDARY, FCSEP))  # '.' will not match special chars
            tok = "%s%s%s%s%s%s" % (left, O_BOUNDARY, tok, C_BOUNDARY, right, quantifier)
            regex.append(tok)
        regex = "(" + "".join(regex) + ")"
        return re.compile(regex, re.UNICODE)

    #TODO: cytonize it !
    @staticmethod
    def tokseq_to_str(wordform_list):
        """ Convert a token sequence to a unicode string
        #seq
        >>> Module.tokseq_to_str([Token(form=u'bla', category=u'WTOKEN'), Token(form=u'bla', category=u'WTOKEN')])
        u'\ue000bla\ue002WTOKEN\ue001\ue000bla\ue002WTOKEN\ue001'
        """
        return "".join(["%s%s%s" % (O_BOUNDARY, FCSEP.join([wordform.form, wordform.pos]), C_BOUNDARY) for wordform in wordform_list])

    #TODO: cytonize it !
    @staticmethod
    def str_to_tokseq(inputstring):
        """ Convert an unicode string to a token sequence
        
        >>> Module.str_to_tokseq(u'\ue000bla\ue002WTOKEN\ue001\ue000bla\ue002WTOKEN\ue001')
        [Token(form=u'bla', category=u'WTOKEN'), Token(form=u'bla', category=u'WTOKEN')]
        """
        inputstring = inputstring.replace(C_BOUNDARY, "")
        ret = []
        for tokstr in inputstring.split(O_BOUNDARY):
            if (tokstr and FCSEP in tokstr):
                form, cat = tokstr.split(FCSEP)
                wf = Wordform(form, cat)
                ret.append(wf)
            ##else:
            ##    ret.append(Wordform(tokstr, ""))
        return ret



    @staticmethod
    def prettify(s):
        """ Pretty view of a token sequence string (output of :func:`tokseq_to_str`).
        Debug method
        """
        return s.replace(O_BOUNDARY,"~(").replace(C_BOUNDARY,")~").replace(FCSEP, "/")

    def print_regexps(self):
        u""" Debug method: print the regexp of the module

        >>> fitler = Module("([0-9]+/.*)", lambda tokseq: [Token(token.form, "DIGIT") for token in tokseq])
        >>> fitler.print_regexps()
        ((?:~([0-9]+/[^~()~/]*)~))
        """
        print Module.prettify(self.re.pattern)

    def __call__(self, tokseq):
        """ Apply the module on a sequence of token

        :param line: a list of Token
        :returns: a list of Token
        """
        inputstr = Module.tokseq_to_str(tokseq)
        regex = self.re
        convertor = self.convertor
        m = regex.search(inputstr)
        cursor = 0
        new_tokseq = []
        for m in regex.finditer(inputstr):
            begin, end = m.span()
            if begin == end:
                continue
            if begin > cursor:
                #unmatched part
                new_tokseq.extend(Module.str_to_tokseq(inputstr[cursor:begin]))
            new_tokseq.extend(convertor(Module.str_to_tokseq(inputstr[begin:end])))
            cursor = end

        if cursor < len(inputstr):
            #unmatched end
            new_tokseq.extend(Module.str_to_tokseq(inputstr[cursor:]))
            # print str(i),"unmatched", Module.prettify(inputstr[cursor:])
        return new_tokseq


class TokenCategorizer(Composable):
    """ add a type to each token in a list of tokens
    """

    def __init__(self):
        super(TokenCategorizer, self).__init__()
 
    def guess_category(self, token):
        u""" Determine the type of list of char Token
        >>> TokenCategorizer([Token(u'1', u'')])
        [Token(form=u'1', category='DIGIT')]
        >>> TokenCategorizer([Token(u'a', u'')])
        [Token(form=u'a', category='LATIN')]
        >>> TokenCategorizer([Token(u'!', u'')])
        [Token(form=u'!', category='PUNCT')]
        >>> TokenCategorizer([Token(u'\\n', u'')])
        [Token(form=u'\\n', category='nonchar')]
        >>> TokenCategorizer([Token(u'好', u'')])
        [Token(form=u'\\u597d', category='CJK')]
        """
        cat=""
        for char in token.form:
            try:
                name = ud.name(char)
            except ValueError:
                return "nonchar"
            if "CJK" in name:
                if cat and cat != "CJK":
                    return "mixed"
                cat = "CJK"
            if "LATIN" in name:
                if cat and cat != "LATIN":
                    return "mixed"
                cat = "LATIN"
            if "DIGIT" in name:
                if cat and cat != "DIGIT":
                    return "mixed"
                cat = "DIGIT"
            if any([x in name for x in UNIPUNCT]):
                if cat and cat != "DIGIT":
                    return "mixed"
                cat = "PUNCT"
        return cat


    def __call__(self, toklist):
        for tok in toklist:
            tok.category = self.guess_category(tok)
        return toklist

class TokenToWordform(Composable):
    """ Convert a token in a Wordform
    """

    def __init__(self):
        super(TokenToWordform, self).__init__()

    def __call__(self, tokens):
        return [Wordform(token.form, token.category) for token in tokens]


def isPunct(token):
    """ Wether a token is punctuation
    
    >>> isPunct(Token(form=u'bla', category=u'WTOKEN'))
    False
    >>> isPunct(Token(form=u',', category=u'WTOKEN'))
    True
    >>> isPunct(Token(form=u'.', category=u'WTOKEN'))
    True
    >>> isPunct(Token(form=u'!', category=u'WTOKEN'))
    True
    >>> isPunct(Token(form=u' ', category=u'WTOKEN'))
    True
    >>> isPunct(Token(form=u'ab,', category=u'WTOKEN'))
    False
    """
    for letter in list(token.form):
        try:
            name = ud.name(letter)
        except:
            return False
        if any([x in name for x in UNIPUNCT]):
            continue
        else:
            return False
    return True       

def joinForms(category, minlength=1, sep=TOKSEP):
    u""" Create a function that merge tokens in an unique token with the given category

    >>> merge = joinForms("MERGED", minlength=1)
    >>> merge([Token(form=u'bla', category=u'WTOKEN'), Token(form=u'bla', category=u'WTOKEN')])
    [Token(form=u'bla\\ue003bla', category='MERGED')]
    """
    def fct(seq):
        if len(seq) < minlength:
            return seq
        else:
            return [Wordform(sep.join([w.form for w in seq]), category)]
    return fct


#  basic modules

#TokenCategorizer = Module("./.*", TokenCategorizer)

numbers = Module("(./DIGIT)+", joinForms("NUM"))

latin_words = Module("(./LATIN)+", joinForms("WLATIN"))

hanzi_sequence = Module("(./CJK)+", joinForms("unsegmented", 2))

ordinals = Module(u"第/.* .*/NUM", joinForms("ORDINAL"))

var_zhdigits = u"[零一二三四五六七八九十〇]"
var_zhordinals = u"[十百千萬億]"
var_point = u"[點]"

datetime_vars = {
        'year':  u'年/CJK',
        'month': u'月/CJK',
        'day':   u'[日號]/CJK',
        'hour':  u'[時點]/CJK',
        'minute': u'分/.* (鐘/.*)?',
        'second': u'秒/CJK',
        'dayperiod': u'(凌/CJK 晨/CJK | 早/CJK 上/CJK | 上/CJK 午/CJK | 中/CJK 午/CJK | 下/CJK 午/CJK | 晚/CJK 上/CJK)',
        'n24': u'((十/CJK)? {digit}/CJK | ([1１]/DIGIT)? ./DIGIT | 二/CJK 十/CJK [一二三四]/CJK | [２2]/CJK [0-4０-４]/CJK)'.format(digit=var_zhdigits),
        'n31': u'((二/CJK)? (十/CJK)? {digit}/CJK | ([012０１２]/DIGIT)? ./DIGIT | 三/CJK 十/CJK (一/CJK)? | [３3]/DIGIT [01０１]/DIGIT)'.format(digit=var_zhdigits),
        'n12': u'(([０0]/DIGIT)? ./DIGIT | 十/CJK ([一二]/CJK)? | [１1]/DIGIT [012０１２]/DIGIT | {digit}/CJK)'.format(digit=var_zhdigits),
        'n60': u'(([0-5０-５]/DIGIT)? ./DIGIT | ([一二三四五]/CJK)? (十/CJK)? {digit}/CJK)'.format(digit=var_zhdigits)}

re_date = ur"({n12} {month})? ({n31} {day})?".format(**datetime_vars)
re_time = ur"({dayperiod})? ({n24} {hour})? ({n60} {minute})? ({n60} {second})?".format(**datetime_vars)

datetime = Module(" ".join([re_date, re_time]), joinForms("DATETIME", 1))

mini_datetime = Module(ur"{n12} {month} {n31} {day}".format(**datetime_vars), joinForms("DATETIME"))

zhnum = Module(u"({digit}/CJK) (({ord}/CJK)? ({digit}/CJK)?)+ ({point}/.* (({digit}/.*)? ({ord}/.*)?)+)".format(point=var_point, digit=var_zhdigits, ord=var_zhordinals), joinForms("NUM"))

re_url = u" http/WLATIN :/.* //.* //.* (.*/WLATIN ./.*)* .+/WLATIN (//.* .+/WLATIN)*"

url = Module(re_url, joinForms("URL"))


donothing = Module(u"(.*/.*)+", joinForms("unsegmented"))


######## FR et autres langues à espace

mark_punct = Module(ur"(.*/WTOKEN)", lambda x: joinForms("PUNCT")(x) if len(x)==1 and isPunct(x[0]) else x)

mark_numbers = Module(ur"([0-9]+/.*)", joinForms("NUM"))

merge_others = Module(ur"(.*/WTOKEN)+", joinForms("unsegmented"))


####
# Engines: initial tokeniser + processing modules

class Engine(Composable):
    """ Tokenisation engine that :
    * tokenise on each caracter OR on words separated by space
    * apply a sequence of :class:`Modules`
    """

    def __init__(self, modules=None, tokeniser=None, enc="utf8"):
        """
        :param modules: a list of token sequence processing module
        :param tokeniser: an initial (simple) sentence tokeniser
        """
        super(Engine, self).__init__()
        if tokeniser is None:
            tokeniser = CharAsToken() # zh by default
        self.tokeniser = tokeniser
        # other processing
        if modules is None:
            modules = lambda x:x
        else:
            mod = modules[0]
            for msuiv in modules[1:]:
                mod = mod | msuiv
            modules = mod
        self.modules = modules
        self.enc = enc  #TODO: encoding may be only given to "apply_to_file"

    def apply_to_file(self, infile):
        u""" Read a file one line at a time and yield token sequences
        """
        with codecs.open(infile, "r", self.enc) as instream:
            for tokseq in self(instream):
                yield tokseq

    def apply(self, input_lines):
        u""" Same as :func:`call`, backward compatibility
        """
        return self(input_lines)

    def __call__(self, input_lines):
        u""" Apply the tokenisation engine to a sequence (generator) of lines
        
        :param input_lines: list/generator of unicode string to tokenise
        :returns: iterator of lists of Tokens (one list by line)
        """
        #TODO: this may be done in // as each line may be processed independently
        for line in input_lines:
            yield self.apply_on_string(line)

    def preprocess_string(self, input_str):
        return self.apply_on_string(input_str)

    def apply_on_string(self, input_str):
        u""" Tokenise and preprocess a simple string

        The string should be at least a sentence, it may be a full document, a
        paragraph...

        >>> eng = Engine()
        >>> eng.apply_on_string("abc")
        [Token(form=[u'a'], category=''), Token(form=[u'b'], category=''), Token(form=[u'c'], category='')]
        """

        tokseq = self.tokeniser(input_str)
        #tokstr = Module.tokseq_to_str(tokseq)
        tokseq = self.modules(tokseq)
        #WARNING 'splitform' call here to separate initial tokenisation insided (merged) tokens
        return [splitform(tok) for tok in tokseq]

    def print_regexps(self):
        u""" Debug method: print the regexp of each processing module

        >>> eng = Engine(modules=[TokenCategorizer, numbers])
        >>> eng.print_regexps()
        (~([^~()~/]/[^~()~/]*)~)
        ((?:~([^~()~/]/DIGIT)~)+)
        """
        for module in self.modules:
            if type(module) is Module:
                module.print_regexps()

#  default engines (also serve as exemple)

engine_basic = Engine([TokenCategorizer(), TokenToWordform(), Module("(A/LATIN)+ B/LATIN", joinForms("AAB")), Module("([a-zA-Z]*/AAB)+", joinForms("2AB"))])

engine_nothing = Engine([TokenToWordform(), donothing])
engine_default = Engine([TokenCategorizer(), TokenToWordform(), datetime, numbers, latin_words, hanzi_sequence])
#engine_default = Engine([tokenCategorizer(), numbers, latin_words, hanzi_sequence])
#engine_basic = Engine([TokenCategorizer(), numbers])
engine_test = Engine([TokenCategorizer(), TokenToWordform() ])

# datetime, numbers, zhnum, hanzi_sequence, latin_words, ordinals, url])

engine_words = Engine([TokenToWordform(), merge_others], WordAsToken())
engine_words_punct = Engine([TokenToWordform(), mark_punct, merge_others], WordAsToken())

def extractKeywords(wordlist, catname="KEYWORD", sep=""):
    def f(tokseq):
        for word in wordlist:
            result = []
            for tok in tokseq:
                forms = tok.form.split(word)
                for i, form in enumerate(forms):
                    if len(form) > 0:
                        result.append(Token(form,tok.category))
                    if i < len(forms)-1:
                        result.append(Token(word.replace(sep,""),catname))
            tokseq = result
        return tokseq
    return f

def engine_from_keywords(wordlist):
    kword_module = Module(".*/unsegmented", extractKeywords(wordlist))
    return Engine([TokenCategorizer(), datetime, numbers, zhnum, hanzi_sequence, latin_words, ordinals, url, kword_module])



def preprocess_string(text, engine=engine_default):
    for l in text.split("\n"):
        tokseq = engine.preprocess_string(text)
        yield tokseq


