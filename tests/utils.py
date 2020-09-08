import random

EPSILON = 0.0001


def float_equal(a, b):
    return (a != a and b != b) or abs(a - b) < EPSILON


def random_ngram(size):
    return [int(random.paretovariate(0.8)) for _ in range(size)]


def generate_random_ngrams(nb=1000, size=3):
    """ Generate list of random n-grams (of int)
    """
    return [random_ngram(size) for _ in range(int(nb))]


def compare_node(ngram, ref_trie, test_trie):
    """ Fails if the results of any measure is different for the query of a specific ngram
    """
    measures = ["query_count", "query_entropy", "query_ev", "query_autonomy"]

    for measure in measures:
        # print("Compare on measure: %s" % measure)
        try:
            m_ref = getattr(ref_trie, measure)(ngram)
        except Exception as e:  # if exception check that other also raise exception
            print("(trie: %s) exception raised for: %s" % (type(ref_trie), ngram))
            print(e)
            with pytest.raises(type(e)):
                getattr(test_trie, measure)(ngram)
        else:
            m_test = getattr(test_trie, measure)(ngram)
            assert float_equal(m_ref, m_test), "%s different for ngram %s" % (
                measure,
                ngram,
            )
