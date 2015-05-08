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

        try:
            self.root = self.graph.cypher.execute("MATCH (r:RootNode) RETURN ID(r)")[0][0]
        except IndexError:
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
            r = self.graph.cypher.execute("MATCH (s)-[:Child {token: t}]->(c) WHERE id(s) = %i RETURN t, ID(c)" % node)
            for token, child in r:
                yield from _rec(child, ngram + [token])
        _rec(self.root, [])

    def update_stats(self):
        """ Update the internal statistics (like entropy, and variance & means
        for the entropy variations. """
        if not self.dirty:
            return

        for i in range(self.depth, -1, -1):
            for r, s in self.graph.cypher.execute("MATCH (:RootNode)-[r:Child*%i]->(s) RETURN r, ID(s)" % i if i else "MATCH (:RootNode)-[r:Child]->(s) RETURN r, ID(s)"):
                e = entropy(j[0] for j in self.graph.cypher.execute("MATCH (s)-[:Child]->(c) WHERE ID(s) = %i RETURN c.count" % s))
                self.graph.cypher.execute("MATCH (s) WHERE id(s) = %i SET s.entropy = %s" % (s, e))

        for i in range(self.depth):
            mean = self.graph.cypher.execute("MATCH (:RootNode)-[r:Child*%s]->(s) RETURN avg(s.entropy - last(r).entropy)" % (i + 1))
            stdev = self.graph.cypher.execute("MATCH (:RootNode)-[r:Child*%s]->(s) RETURN stdev(s.entropy - last(r).entropy)" % (i + 1))
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

        self.graph.cypher.execute("MATCH (s) WHERE id(s) = %i SET s.count = s.count + %s" % (node, freq))

        try:
            token = ngram[0]
        except IndexError:
            r = self.graph.cypher.execute("MATCH (s)-[:Document {docid: %s}]->(r) WHERE id(s) = %i SET r.count = r.count + %s RETURN r" % (docid, node, freq))
            if len(r):
                assert len(r) == 1
            else:
                self.graph.cypher.execute("MATCH (n) WHERE id(n) = %i CREATE n-[:Document {docid: %s}]->(r {count: %s})" % (node, docid, freq))
            return

        try:
            child = self.graph.cypher.execute("MATCH (s)-[:Child {token: '%s'}]->(c) WHERE id(s) = %i RETURN ID(c)" % (token, node))[0][0]
        except IndexError:
            child = self.graph.cypher.execute("MATCH (s) WHERE id(s) = %i CREATE (s)-[:Child {token: '%s'}]->(r {count: 0}) RETURN ID(r)" % (node, token))[0][0]

        # recurse, add the end of the ngram
        self._add_ngram(child, ngram[1:], docid, freq)

    def query_node(self, ngram):
        """ Return a tuple with the main node data : (count, entropy).
        Count is the number of ngrams starting with the ``ngram`` parameter, entropy the entropy after the ngram.
        """
        self._check_dirty()

        q = "(:RootNode)" + '()'.join("-[:Child {token: '%s'}]->" % token for token in ngram) + "(leaf)"
        count, entropy = self.graph.cypher.execute("MATCH %s RETURN leaf.count, leaf.entropy" % q)[0]

        return (count, entropy)

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
