import math
import operator
import random

from eleve.storage.memory import MemoryTrie

def entropy(counts):
    s = sum(counts)
    return -sum(map(lambda x: (x/s)*math.log2(x/s), counts))

def mean_variance(values):
    a = 0
    q = 0
    k = 0
    for v in values:
        k += 1
        old_a = a
        a += (v - a) / k
        q += (v - old_a)*(v - a)
    return (a, math.sqrt(q / k))

def test_integrity(memtrie):
    
    # check the integrity of the tree, the correctness of entropy...

    def ngrams_size(root, size, path=[]):
        if size == 0:
            yield path
        else:
            for k, child in root.childs.items():
                yield from ngrams_size(child, size - 1, path + [k])

    mvl_cache = {}
    def mv_level(s):
        if s in mvl_cache:
            return mvl_cache[s]
        mvl_cache[s] = mean_variance(map(memtrie.query_ev, ngrams_size(memtrie.root, s)))
        return mvl_cache[s]

    def rec_integrity(node, ngram):
        # counts
        count_childs = list(map(operator.attrgetter('count'), node.childs.values()))
        assert sum(count_childs) in (node.count, 0)

        assert (node.count, node.entropy) == memtrie.query_node(ngram)

        if len(node.childs):
            assert abs(entropy(count_childs) - node.entropy) < 1e-6

        if ngram and len(node.childs):
            ev = memtrie.query_ev(ngram)
            assert ev == node.entropy - memtrie.query_node(ngram[:-1])[1]

            mean, variance = mv_level(len(ngram))
            l = len(list(ngrams_size(memtrie.root, len(ngram))))

            autonomy = (ev - mean) / 1
            assert abs(autonomy - memtrie.query_autonomy(ngram)) < 1e-6, (autonomy, memtrie.query_autonomy(ngram))

        for k, child in node.childs.items():
            rec_integrity(child, ngram + [k])

    rec_integrity(memtrie.root, [])

def generate_random_trie():
    depth = random.randint(2,5)
    m = MemoryTrie(depth)

    def add(prefix):
        for i in range(int(random.expovariate(0.1) + 1)):
            k = int(random.gauss(0, 7))
            if len(prefix) < depth - 1:
                add(prefix + [k])
            else:
                m.add_ngram(prefix + [k])

    add([])
    return m

if __name__ == '__main__':
    t = generate_random_trie()
    test_integrity(t)
