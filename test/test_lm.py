from eleve.lm import LM

def test_basic_segmentation():
    l = LM(2)
    l.add_sentence(['je', 'vous', 'parle', 'de', 'hot', 'dog'])
    l.add_sentence(['j', 'ador', 'les', 'hot', 'dog'])
    l.add_sentence(['hot', 'dog', 'ou', 'pas'])
    l.add_sentence(['hot', 'dog', 'ou', 'sandwich'])

    assert l.segment(['je', 'deteste', 'les', 'hot', 'dog']) == [['je'], ['deteste'], ['les'], ['hot', 'dog']]
    #assert l.segment(['je', 'deteste', 'les', 'sandwich']) == [['je'], ['deteste'], ['les'], ['sandwich']]
    assert l.segment(['je', 'vous', 'ou', 'hot', 'dog']) == [['je', 'vous'], ['ou'], ['hot', 'dog']]
