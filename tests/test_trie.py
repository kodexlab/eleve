import pytest
import random
import tempfile
import shutil

from eleve.memory import MemoryTrie
from eleve.c_memory.cmemory import MemoryTrie as CMemoryTrie
from eleve.leveldb import LeveldbTrie as PyLeveldbTrie
from eleve.c_leveldb.cleveldb import LeveldbTrie as CLeveldbTrie


@pytest.fixture
def trie(request):
    if request.param == "pyram":
        return MemoryTrie()
    elif request.param == "cram":
        return CMemoryTrie()
    elif request.param == "pyleveldb":
        fs_path = tempfile.mkdtemp(prefix="tmp_eleve_pyldb_")
        trie = PyLeveldbTrie(path=fs_path)
        def fin():
            print ("teardown pyleveldb")
            shutil.rmtree(fs_path)
        request.addfinalizer(fin)
    elif request.param == "cleveldb":
        fs_path = tempfile.mkdtemp(prefix="tmp_eleve_cldb_")
        trie = CLeveldbTrie(path=fs_path)
        def fin():
            print ("teardown cleveldb")
            shutil.rmtree(fs_path)
        request.addfinalizer(fin)
    else:
        raise ValueError("invalid internal test config")
    return trie


all_backends = ["pyram", "cram", "pyleveldb", "cleveldb"]
tested_backends = ["cram", "pyleveldb", "cleveldb"] # against pyram
EPSILON = 0.0001


def float_equal(a, b):
    return (a != a and b != b) or abs(a - b) < EPSILON

def generate_random_ngrams():
    """ Generate list of random n-grams (of int)
    """
    depth = random.randint(3,4)
    m = []

    def add(prefix):
        for i in range(int(random.expovariate(0.1) + 1)):
            k = int(random.expovariate(0.1))
            if len(prefix) < depth - 1:
                add(prefix + [k])
            else:
                m.append(prefix + [k])

    add([])
    random.shuffle(m)
    return m


def compare_node(ngram, ref_trie, test_trie):
    """ Fails if the results of any measure is different for the query of a specific ngram
    """
    measures = ['query_count', 'query_entropy', 'query_ev', 'query_autonomy']

    for measure in measures:
        #print("Compare on measure: %s" % measure)
        try:
            m_ref = getattr(ref_trie, measure)(ngram)
        except Exception as e:  # if exception check that other also raise exception
            print("(trie: %s) exception raised for: %s" % (type(ref_trie), ngram))
            print(e)
            with pytest.raises(type(e)):
                getattr(test_trie, measure)(ngram)
        else:
            m_test = getattr(test_trie, measure)(ngram)
            assert float_equal(m_ref, m_test), "%s different for ngram %s" % (measure, ngram)


def compare_nodes(ngrams, ref_trie, test_trie):
    # compare root
    compare_node([], ref_trie, test_trie)
    # compare random node, may not existe (check exception)
    compare_node([420001337] * 10, ref_trie, test_trie)
    # compare all ngrams
    for n in ngrams:
        for i in range(len(n)):
            compare_node(n[:i+1], ref_trie, test_trie)
            # try a non-existent node:  should raise exception in both case
            compare_node(n[:i] + [420001337], ref_trie, test_trie)
        compare_node(n + [420001337], ref_trie, test_trie) # try a non-existent node



@pytest.mark.parametrize("trie", all_backends, indirect=True)
def test_basic_trie(trie):
    """ Minimal test on simple example
    """
    trie.clear()
    LE, PETIT, GROS, CHAT, CHIEN, RAT = range(1, 7)

    trie.add_ngram([LE,PETIT,CHAT])
    trie.add_ngram([LE,PETIT,CHIEN])
    trie.add_ngram([LE,PETIT,RAT])
    trie.add_ngram([LE,GROS,RAT])
    assert trie.query_count([LE, PETIT]) == 3
    assert float_equal(trie.query_entropy([LE, PETIT]), 1.584962500721156)
    assert float_equal(trie.query_autonomy([LE, PETIT]), 1.0)
    assert trie.query_count([]) == 4

    # test removing a n-gramm
    trie.add_ngram([LE,PETIT,CHAT], -1)
    assert trie.query_count([LE, PETIT]) == 2
    assert float_equal(trie.query_entropy([LE, PETIT]), 1.0)
    assert float_equal(trie.query_autonomy([LE, PETIT]), 1.0)


@pytest.mark.parametrize("trie", all_backends, indirect=True)
def test_robustness(trie):
    """ Test robustness of Tries
    """
    trie.clear()
    
    #XXX seg fault for now : #16 https://git.kodexlab.com/kodexlab/eleve/issues/16
    #with pytest.raises(ValueError):
    #    trie.add_ngram([])
    with pytest.raises(ValueError):
        trie.add_ngram(["oneword"])


@pytest.mark.parametrize("trie", tested_backends, indirect=True)
def test_trie_class(trie, reference_class=MemoryTrie):
    """ Compare implementation against reference class (on random ngrams lists)
    """
    ngrams = generate_random_ngrams()
    ref_trie = reference_class()

    trie.clear()
    ref_trie.clear()

    for i, n in enumerate(ngrams):
        trie.add_ngram(n)
        ref_trie.add_ngram(n)
        if i % (len(ngrams) // 3) == 0:
            compare_nodes(ngrams, ref_trie, trie)
    compare_nodes(ngrams, ref_trie, trie)

