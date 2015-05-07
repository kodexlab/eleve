from __future__ import division
import sys
import logging
from py2neo import Graph

from eleve.storage import Storage
from eleve.memory import entropy

class Neo4jStorage(Storage):
    """ Neo4j storage
    """

    def __init__(self, depth):
        """
        :param depth: Maximum length of stored ngrams

        >>> s = Neo4jStorage(4)
        """
        self.graph = Graph()

        # delete everything
        self.graph.cypher.execute("MATCH (n) OPTIONAL MATCH (n)-[r]-() DELETE n,r")

        self.root = self.graph.cypher.execute("MATCH (r:RootNode) RETURN ID(r)")[0][0]
        if not self.root:
            logging.info("Unable to find the root of the trie, creating it.")
            self.root = self.graph.cypher.execute("CREATE (r:RootNode) RETURN ID(r)")[0][0]

        self.depth = depth

        self.normalization = [(0,0)] * depth

        self.dirty = False

    @classmethod
    def load(cls, path):
        raise NotImplementedError()

    def save(self, path):
        raise NotImplementedError()

    def __iter__(self):
        """ Iterator on all the ngrams in the trie.
        Including partial ngrams (not leafs). So it gives a ngram for every node.
        """
        def _rec(node, ngram):
            yield ngram
            r = self.graph.cypher.execute("MATCH (s)-[{token: t}]->(c) WHERE id(s) = %s RETURN t, ID(c)" % node)
            for token, child in r:
                yield from _rec(child, ngram + [token])
        _rec(self.root, [])

    def update_stats(self):
        """ Update the internal statistics (like entropy, and variance & means
        for the entropy variations. """
        if not self.dirty:
            return

        for i in range(self.depth - 1, -2, -1):
            for r, s in self.graph.cypher.execute("MATCH (:RootNode)-[r*%s]->(s) RETURN r, ID(s)" % (i + 1)):
                e = entropy(j[0] for j in self.graph.cypher.execute("MATCH nodeid(s)->(c) RETURN c.count"))
                self.graph.cypher.execute("MATCH (s) WHERE id(s) = %s SET s.entropy = %s" % (s, e))

        for i in range(self.depth):
            mean = self.graph.cypher.execute("MATCH (:RootNode)-[r*%s]->(s) RETURN avg(s.entropy - r[-1].entropy)" % (i + 1))
            stdev = self.graph.cypher.execute("MATCH (:RootNode)-[r*%s]->(s) RETURN stdev(s.entropy - r[-1].entropy)" % (i + 1))
            self.normalization[i] = (mean, stdev)

        self.dirty = False

    def _check_dirty(self):
        if self.dirty:
            logging.warning("Updating the tree statistics (update_stats method), as we query it while dirty. This is a slow operation.")
            self.update_stats()

    def add_ngram(self, ngram, docid, freq=1):
        """ Add a ngram to the tree.
        You can specify the number of times you add (or substract) that ngram by using the `freq` argument.
        """

        if len(ngram) > self.depth:
            raise ValueError("The size of the ngram parameter must be less or equal than depth ({})".format(self.depth))

        self._add_ngram(self.root, ngram, docid, freq)
        self.dirty = True

    def _add_ngram(self, node, ngram, docid, freq):
        """ Recursive function used to add a ngram.
        """

        self.graph.cypher.execute("MATCH (s) WHERE id(s) = %s SET s.count = s.count + %s" % (node, freq))

        try:
            token = ngram[0]
        except IndexError:
            r = self.graph.cypher.execute("MATCH (s)-[{docid: %s}]->(r) WHERE id(s) = %s SET r.freq = r.freq + %s RETURN r" % (docid, node, freq))
            if len(r):
                assert len(r) == 1
            else:
                self.graph.cypher.execute("MATCH (n) WHERE id(n) = %s CREATE n-[:RELTYPE {docid: %s}]->(r {freq: %s})" % (node, docid, freq))
            return

        try:
            child = self.graph.cypher.execute("MATCH (s)-[{token: '%s'}]->(c) WHERE id(s) = %s RETURN ID(c)" % (token, node))[0][0]
        except IndexError:
            child = self.graph.cypher.execute("MATCH (s) WHERE id(s) = %s CREATE (s)-[:RELTYPE]->(r {count: 0, token: '%s'}) RETURN ID(r)" % (node, token))[0][0]

        # recurse, add the end of the ngram
        self._add_ngram(child, ngram[1:], docid, freq)

    def query_node(self, ngram):
        """ Return a tuple with the main node data : (count, entropy).
        Count is the number of ngrams starting with the ``ngram`` parameter, entropy the entropy after the ngram.
        """
        self._check_dirty()

        q = "(:RootNode)" + '()'.join("-[{token: '%s'}]->" % token for token in ngram) + "(leaf)"
        node = self.graph.cypher.execute("MATCH %s RETURN leaf" % q)[0]

        return (node.count, node.entropy)

    def query_ev(self, ngram):
        """ Return the entropy variation for the ngram.
        """
        node_entropy = self.query_node(ngram)[1]
        parent_entropy = self.query_node(ngram[:-1])[1]

        return node_entropy - parent_entropy

    def query_autonomy(self, ngram, z_score=True):
        """ Return the autonomy (normalized entropy variation) for the ngram.
        """
        self._check_dirty()
        mean, variance = self.normalization[len(ngram) - 1]
        nev = self.query_ev(ngram) - mean
        if z_score:
            nev /= variance
        return nev

if __name__ == '__main__':
    import doctest
    doctest.testmod()
