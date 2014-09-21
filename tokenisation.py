# -*- coding:utf8 -*-

import re
from collections import namedtuple
import codecs

import unicodedata as ud

Token = namedtuple("Token", "form category")
Module = namedtuple("Module", "regexp convertor")
OBOUNDARY = u"\ue000"
CBOUNDARY = u"\ue001"
FCSEP = u"\ue002"
TOKSEP = u"\ue003"

UNIPUNCT = set(['SPACE',
                'SEMICOLON',
                'STOP',
                'MARK',
                'BRACKET',
                'COLON',
                'PARENTHESIS',
                'APOSTROPHE',
                'COMMA'])


def prettify(s):
    return s.replace(BOUNDARY," ").replace(FCSEP, "/")


def tokeniseOnChar(inputstream):
    for line in inputstream:
        yield [Token(c, "") for c in line.strip()] 

def tokeniseOnWord(inputstream):
    for line in inputstream:
        yield [Token(w, "WTOKEN") for w in line.strip().split()]


def tokseq_to_str(tokseq):
    return "".join(["%s%s%s" % (OBOUNDARY, FCSEP.join(tok), CBOUNDARY) for tok in tokseq])

def str_to_tokseq(inputstring):
    """ Convert an unicode string to a token sequence

    >>> Module.str_to_tokseq(u'bla\ue001WTOKEN\ue000bla\ue001WTOKEN')
    [Token(form=u'bla', category=u'WTOKEN'), Token(form=u'bla', category=u'WTOKEN')]
    """
    inputstring = inputstring.replace(CBOUNDARY, "")
    return [Token(*tokstr.split(FCSEP)) \
           for tokstr in inputstring.split(OBOUNDARY) \
            if (tokstr and FCSEP in tokstr)]

def splitform(token):
    return Token(token.form.split(TOKSEP), token.category)

def typeChar(tokseq):
    assert(len(tokseq) == 1)
    token = tokseq[0]
    assert(len(token.form) == 1)
    try:
        name = ud.name(token.form)
    except ValueError:
        return [Token(token.form, "nonchar")]
    if "CJK" in name:
        return [Token(token.form, "CJK")]
    if "LATIN" in name:
        return [Token(token.form, "LATIN")]
    if "DIGIT" in name:
        return [Token(token.form, "DIGIT")]
    if any([x in name for x in UNIPUNCT]):
        return [Token(token.form, "PUNCT")]
    return tokseq

def isPunct(token):
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


def joinForms(category, minlength=1, sep=TOKSEP):
    def f(tokseq):
        if len(tokseq) < minlength:
            return tokseq
        else:
            return [Token(sep.join([t.form for t in tokseq]), category)]
    return f


class Engine(object):
    def __init__(self, modules, wordAsToken=False, enc="utf8"):
        self.modules = modules
        self.wordAsToken = wordAsToken
        self.enc = enc
        self._compile_re()
        self.tokenise = tokeniseOnChar if not wordAsToken else tokeniseOnWord

    def _compile_re(self):
        re_list = []
        for m in self.modules:
            regex = []
            for tok in m.regexp.split():
                if tok.startswith("("):
                    left = "(?:"
                    tok = tok[1:]
                else:
                    left = ""
                if tok[-1] in "?+*" and (len(tok) >= 2 and tok[-2] == ")"):
                    quantifier = tok[-1]
                    tok = tok[:-1]
                else:
                    quantifier = ""
                if tok.endswith(")"):
                    right = tok[-1]
                    tok = tok[:-1]
                else:
                    right = ""
                if "/" in tok:
                    forme, tag = tok.rsplit("/", 1)
                else:
                    forme = tok
                    tag = ".*"
                tok = FCSEP.join([forme,tag])  # set proper FCSEP
                tok = tok.replace(".", "[^%s%s%s]" % (CBOUNDARY, OBOUNDARY, FCSEP))  # '.' will not match special chars
                tok = "%s%s%s%s%s%s" % (left, OBOUNDARY, tok, CBOUNDARY, right, quantifier)
                regex.append(tok)
            regex = "(" + "".join(regex) + ")"
            re_list.append(re.compile(regex, re.UNICODE))
        self.re_list = re_list

    def apply_to_file(self, infile):
        """
        read a file one line at a time
        and yield token sequences
        """
        instream = codecs.open(infile, "r", self.enc)
        for tokseq in self.tokenise(instream):
            tokseq = self._apply(tokseq)
            yield tokseq
        instream.close()

    def apply(self, something):
        """
        preprocess a file or an iterator
        """
        if type(something) == str or type(something) == unicode:
            for tokseq in self.tokenise([something]):
                yield self._apply(tokseq)
        else:
            for tokseq in self.tokenise(something):
                yield self._apply(tokseq)

    def _apply(self, tokseq):
        for i in xrange(len(self.modules)):
            inputstr = tokseq_to_str(tokseq)
            regex = self.re_list[i]
            m = regex.search(inputstr)
            cursor = 0
            newtokseq = []
            for m in regex.finditer(inputstr):
                begin, end = m.span()
                if begin == end:
                    continue
                if begin > cursor:
                    #unmatched part
                    newtokseq.extend(str_to_tokseq(inputstr[cursor:begin]))
                newtokseq.extend(self.modules[i].convertor(str_to_tokseq(inputstr[begin:end])))
                cursor = end

            while False and m and cursor < len(inputstr):
                begin, end = m.span()
                curs2 = cursor
                while begin == end and curs2 < (len(inputstr)):
                    curs2 += 1
                    m = regex.search(inputstr[curs2:])
                    begin, end = m.span()
                begin += curs2 - cursor
                end += curs2 - cursor
                if begin > 0:
                    #unmatched part, rebuild as-is
                    newtokseq.extend(str_to_tokseq(inputstr[cursor:cursor+begin]))
                    # print str(i),"unmatched", prettify(inputstr[cursor:cursor+begin])
                if not begin == end:
                    newtokseq.extend(self.modules[i].convertor(str_to_tokseq(inputstr[cursor+begin:cursor+end])))
                    # print str(i),"matched", prettify(inputstr[cursor+begin:cursor+end])
                cursor = cursor + end
                m = regex.search(inputstr[cursor:])

            if cursor < len(inputstr):
                #unmatched end
                newtokseq.extend(str_to_tokseq(inputstr[cursor:]))
                # print str(i),"unmatched", prettify(inputstr[cursor:])
            tokseq = newtokseq
        return [splitform(tok) for tok in tokseq]

    def print_regexps(self):
        for r in self.re_list:
            print r.pattern.replace(BOUNDARY, " ").replace(FCSEP, "/")

    def preprocess_string(self, s):
        tokseq = tokeniseOnChar([s]).next() if not self.wordAsToken else tokeniseOnWord([s]).next()
        return self._apply(tokseq)


#  basic modules

charTagger = Module("./.*", typeChar)

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
        'n12': u'({digit}/CJK | ([０0]/DIGIT)? ./DIGIT | 十/CJK ([一二]/CJK)? | [１1]/DIGIT [012０１２]/DIGIT)'.format(digit=var_zhdigits),
        'n60': u'(([0-5０-５]/DIGIT)? ./DIGIT | ([一二三四五]/CJK)? (十/CJK)? {digit}/CJK)'.format(digit=var_zhdigits)}

re_datetime = u"({year})? ({n12} {month})? ({n31} {day})? ({dayperiod})? ({n24} {hour})? ({n60} {minute})? ({n60} {second})?".format(**datetime_vars)

datetime = Module(re_datetime, joinForms("DATETIME", 3))

zhnum = Module(u"({digit}/CJK) (({ord}/CJK)? ({digit}/CJK)?)+ ({point}/.* (({digit}/.*)? ({ord}/.*)?)+)".format(point=var_point, digit=var_zhdigits, ord=var_zhordinals), joinForms("NUM"))

re_url = u" http/WLATIN :/.* //.* //.* (.*/WLATIN ./.*)* .+/WLATIN (//.* .+/WLATIN)*"

url = Module(re_url, joinForms("URL"))


donothing = Module(u"(.*/.*)+", joinForms("unsegmented"))


######## FR et autres langues à espace

mark_punct = Module(ur"(.*/WTOKEN)", lambda x: joinForms("PUNCT")(x) if len(x)==1 and  isPunct(x[0]) else x)

merge_others = Module(u"(.*/WTOKEN)+", joinForms("unsegmented"))


#  default engines (also serve as exemple)

engine_nothing = Engine([donothing])
engine_default = Engine([charTagger, datetime, numbers, latin_words, hanzi_sequence])
#engine_default = Engine([charTagger, numbers, latin_words, hanzi_sequence])
engine_basic = Engine([charTagger, numbers])
engine_test = Engine([charTagger, datetime, numbers, zhnum, hanzi_sequence,  latin_words, ordinals, url])

engine_words = Engine([merge_others], wordAsToken=True)
engine_words_punct = Engine([mark_punct, merge_others], wordAsToken=True)


def engine_from_keywords(wordlist):
    kword_module = Module(".*/unsegmented", extractKeywords(wordlist))
    return Engine([charTagger, datetime, numbers, zhnum, hanzi_sequence,  latin_words, ordinals, url, kword_module])




def preprocess_string(text, engine=engine_default):
    for l in text.split("\n"):
        tokseq = engine.preprocess_string(text)
        yield tokseq


