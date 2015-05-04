from lm import LM

def test_basic_segmentation():
    l = LM(2)
    l.add_phrase(['je', 'vous', 'parle', 'de', 'hot', 'dog'])
    l.add_phrase(['j', 'ador', 'les', 'hot', 'dog'])
    l.add_phrase(['hot', 'dog', 'ou', 'pas'])
    l.add_phrase(['hot', 'dog', 'ou', 'sandwich'])

    assert l.segment(['je', 'deteste', 'les', 'hot', 'dog']) == [['je'], ['deteste'], ['les'], ['hot', 'dog']]
    assert l.segment(['je', 'deteste', 'les', 'sandwich']) == [['je'], ['deteste'], ['les'], ['sandwich']]
    assert l.segment(['je', 'vous', 'ou', 'hot', 'dog']) == [['je', 'vous'], ['ou'], ['hot', 'dog']]
