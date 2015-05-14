from __future__ import division
import logging
from py2neo import Graph
import random

from eleve.storage import Storage
from eleve.memory import entropy

class Neo4jStorage(Storage):
    """ Neo4j storage
    """

    def __init__(self, depth, gid=None):
        """
        :param depth: Maximum length of stored ngrams

        >>> s = Neo4jStorage(4)
        """
        self.depth = depth
        self.graph = Graph()
        self.gid = gid if gid is not None else random.randint(0,1000000000)
        self.normalization = [(0,0)] * self.depth
        self.load_root()

    def load_root(self):
        try:
            self.root = self.graph.cypher.execute("MATCH (r:RootNode:Root%s) RETURN ID(r)" % self.gid)[0][0]
        except IndexError:
            self.root = self.graph.cypher.execute_one("CREATE (r:RootNode:Root%s {count: 0, depth: %i}) RETURN ID(r)" % (self.gid, self.depth))
        assert isinstance(self.root, int)
        self.dirty = True

    def clear(self):
        # delete everything
        self.graph.cypher.execute("MATCH (n:RootNode:Root%s) OPTIONAL MATCH (n)-[r]-() DELETE n,r" % self.gid)
        self.load_root()
        return self

    def __iter__(self):
        """ Iterator on all the ngrams in the trie.
        Including partial ngrams (not leafs). So it gives a ngram for every node.
        """
        def _rec(node, ngram):
            yield ngram
            r = self.graph.cypher.stream("MATCH (s)-[r:Child]->(c) WHERE id(s) = %i RETURN r.token, ID(c)" % node)
            for token, child in r:
                yield from _rec(child, ngram + [token])
        yield from _rec(self.root, [])

    def update_stats(self):
        """ Update the internal statistics (like entropy, and variance & means
        for the entropy variations. """
        if not self.dirty:
            return

        for s, in self.graph.cypher.stream("MATCH (r)-[:Child*0..]->(s) WHERE ID(r) = %i RETURN ID(s)" % self.root):
            e = entropy(j[0] for j in self.graph.cypher.stream("MATCH (s)-[:Child]->(c) WHERE ID(s) = %i RETURN c.count" % s))
            # the .10f is because neo4j doesn't handle correctly scientific notation. Example: 1.0e-5
            self.graph.cypher.execute("MATCH (s) WHERE id(s) = %i SET s.entropy = %.10f" % (s, e))

        for i in range(self.depth):
            if i == 0:
                mean, stdev = self.graph.cypher.execute("MATCH (r)-[:Child]->(s) WHERE ID(r) = %i RETURN avg(s.entropy - r.entropy), stdevp(s.entropy - r.entropy)" % self.root)[0]
            else:
                q = 'MATCH (root)' + '-[:Child]->()' * (i - 1) + '-[:Child]->(r)-[:Child]->(s) WHERE ID(root) = %i' % self.root
                mean, stdev = self.graph.cypher.execute(q + " RETURN avg(s.entropy - r.entropy), stdevp(s.entropy - r.entropy)")[0]
            assert mean is not None and stdev is not None
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

        self.graph.cypher.execute("MATCH (s) WHERE id(s) = %i SET s.count = s.count + %.10f" % (node, freq))

        try:
            token = ngram[0]
        except IndexError:
            r = self.graph.cypher.execute("MATCH (s)-[:Document {docid: %s}]->(r) WHERE id(s) = %i SET r.count = r.count + %.10f RETURN r" % (docid, node, freq))
            if len(r):
                assert len(r) == 1
            else:
                self.graph.cypher.execute("MATCH (n) WHERE id(n) = %i CREATE n-[:Document {docid: %s}]->(r {count: %.10f})" % (node, docid, freq))
            return
        
        try:
            child = self.graph.cypher.execute("MATCH (s)-[:Child {token: '%s'}]->(c) WHERE id(s) = %i RETURN ID(c)" % (token, node))[0][0]
        except IndexError:
            child = self.graph.cypher.execute("MATCH (s) WHERE id(s) = %i CREATE (s)-[:Child {token: '%s'}]->(r {count: 0}) RETURN ID(r)" % (node, token))[0][0]

        # recurse, add the end of the ngram
        self._add_ngram(child, ngram[1:], docid, freq)
    
    def _query_node(self, ngram):
        """ Internal function that returns count, entropy and node_id """
        self._check_dirty()

        if ngram:
            q = "(root)" + '()'.join("-[:Child {token: '%s'}]->" % token for token in ngram) + "(leaf)"
            try:
                count, entropy, node_id = self.graph.cypher.execute("MATCH %s WHERE id(root) = %i RETURN leaf.count, leaf.entropy, id(leaf)" % (q, self.root))[0]
            except IndexError:
                return (0., 0., None)
        else:
            count, entropy, node_id = self.graph.cypher.execute("MATCH (root) WHERE id(root) = %i RETURN root.count, root.entropy, id(root)" % self.root)[0]

        return (count, entropy, node_id)

    def query_node(self, ngram):
        """ Return a tuple with the main node data : (count, entropy).
        Count is the number of ngrams starting with the ``ngram`` parameter, entropy the entropy after the ngram.
        """
        return self._query_node(ngram)[:2]

    def query_postings(self, ngram):
        node_id = self._query_node(ngram)
        if node_id is None:
            return
        for docid, count in self.graph.cypher.stream("MATCH (s)-[r:Document]->(l) WHERE id(s) = %i RETURN r.docid, s.count" % node_id):
            yield (docid, count)

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
