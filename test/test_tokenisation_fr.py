#!/usr/bin/env python
#-*- coding:utf-8 -*-
import pytest
from pprint import pprint

from tokenisation_fr import *
from tokenisation_pl import TOKSEP

test_tokeniser_fr_data = [
    (
        [u'Dans cet article, nous comparons la structure topologique des r\xe9seaux lexicaux avec une m\xe9thode fond\xe9e sur des marches al\xe9atoires.'],
        [[([u'Dans', u'cet', u'article'], 'unsegmented'),
         ([u','], u'PUNCT'),
         ([u'nous', u'comparons', u'la', u'structure', u'topologique', u'des',
           u'r\xe9seaux', u'lexicaux', u'avec', u'une', u'm\xe9thode',
           u'fond\xe9e', u'sur', u'des', u'marches', u'al\xe9atoires'],
          'unsegmented'),
         ([u'.'], u'PUNCT')
        ]]
    ),
    (
        [u'Il vent 25 clavier !', u'pour 25,3€'],
        [[([u'Il', u'vent'], 'unsegmented'),
         ([u'25'], u'NUM'),
         ([u'clavier'], 'unsegmented'),
         ([u'!'], u'PUNCT')],
         [([u'pour'], 'unsegmented'),
         ([u'25', u',', u'3', u'\u20ac'], u'PRICE_EURO')]]
    ),
    (
        [u'une idée de sous-titre ?'],
        [[([u'une', u'id\xe9e', u'de', u'sous-titre'], 'unsegmented'),
          ([u'?'], u'PUNCT')]
        ]
    ),
    (
        [u'la construction d’un Wordnet Libre du Fran\u00e7ais (WOLF)'],
        [[([u'la',
            u'construction',
            u'd\u2019',
            u'un',
            u'Wordnet',
            u'Libre',
            u'du',
            u'Fran\xe7ais'],
           'unsegmented'),
          ([u'('], u'PUNCT'),
          ([u'WOLF'], 'unsegmented'),
          ([u')'], u'PUNCT')]
        ]
    ),
]

# test the full engine
@pytest.mark.parametrize("input, expected", test_tokeniser_fr_data)
def test_tokeniser_fr(input, expected):
    results = list(tokeniser_fr(input))
    pprint( [[(tok.form, tok.category) for tok in tokseq] for tokseq in results] )
    assert results == expected

modules_tests = [
    
    (   # module pour tagé les ponctuation
        mark_punct, [
            (
                [(u'abc', u'WTOKEN'), (u'test', u'WTOKEN')],
                [(u'abc', u'WTOKEN'), (u'test', u'WTOKEN')]
            ),
            (
                [(u'abc', u'WTOKEN'), (u',', u'WTOKEN')],
                [(u'abc', u'WTOKEN'), (u',', u'PUNCT')]
            ),
            (
                [(u'1354', u'WTOKEN')],
                [(u'1354', u'WTOKEN')]
            ),
        ]
    ),
    (   # module pour tagé les nombres
        mark_numbers, [
            (
                [(u'1354', u'WTOKEN')],
                [(u'1354', u'NUM')]
            ),
            (
                [(u'1354', u'WTOKEN'), (u',', u'PUNCT'), (u'99', u'WTOKEN'), ],
                [(u'1354'+TOKSEP+u','+TOKSEP+u'99', u'NUM')]
            ),
            (
                [(u'abc', u'WTOKEN'), (u'test', u'WTOKEN')],
                [(u'abc', u'WTOKEN'), (u'test', u'WTOKEN')]
            ),
            (
                [(u'abc', u'WTOKEN'), (u'1', u'WTOKEN')],
                [(u'abc', u'WTOKEN'), (u'1', u'NUM')]
            ),
            (
                [(u'A4', u'WTOKEN'), (u'18h50', u'WTOKEN')],
                [(u'A4', u'WTOKEN'), (u'18h50', u'WTOKEN')]
            ),
            (
                [(u'1354', u'WTOKEN'), (u',', u'WTOKEN'), (u'45', u'WTOKEN')],
                [(u'1354', u'NUM'), (u',', u'WTOKEN'), (u'45', u'NUM')]
            ),
            (
                [(u'1354', u'WTOKEN'), (u',', u'WTOKEN'), (u'45', u'WTOKEN')],
                [(u'1354', u'NUM'), (u',', u'WTOKEN'), (u'45', u'NUM')]
            ),
        ]
    ),
    (
        mark_price_euro, [
            (
                [(u'1354', u'NUM'), (u'€', u'WTOKEN')],
                [(u'1354'+TOKSEP+u'\u20ac', 'PRICE_EURO')]
            ),
            (
                [(u'85'+TOKSEP+u','+TOKSEP+u'99', u'NUM'), (u'€', u'WTOKEN')],
                [(u'85'+TOKSEP+u','+TOKSEP+u'99'+TOKSEP+u'\u20ac', 'PRICE_EURO')]
            ),
        ]
    ),
]

_modules_tests = [(module, input, expected) \
                        for (module, inexp) in modules_tests \
                        for (input, expected) in inexp]

# run the tests
@pytest.mark.parametrize("module, input, expected", _modules_tests)
def test_all_module(module, input, expected):
    print module.tokseq_to_str(input)
    module.print_regexps()
    result = module(input)
    pprint(result)
    assert result == expected


