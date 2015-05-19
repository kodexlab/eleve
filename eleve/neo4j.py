from __future__ import division
import logging
from py2neo import Graph
import random
import sys

from eleve.storage import Storage
from eleve.memory import entropy

class Neo4jStorage(Storage):
    """ Neo4j storage
    """

    def __init__(self, depth, gid=None):
        """
        :param depth: Maximum length of stored ngrams
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
        tx = self.graph.cypher.begin()
        tx.append("MATCH (:RootNode:Root%s)-[r*]->(n) delete last(r),n" % self.gid)
        tx.append("MATCH (n:RootNode:Root%s) delete n" % self.gid)
        tx.commit()
        self.load_root()
        return self

    def __iter__(self):
        """ Iterator on all the ngrams in the trie.
        Including partial ngrams (not leafs). So it gives a ngram for every node.
        """
        def _rec(node, ngram):
            yield ngram
            r = self.graph.cypher.stream("MATCH (s)-[r:Child]->(c) WHERE id(s) = {nid} RETURN r.token, ID(c)", {'nid': node})
            for token, child in r:
                yield from _rec(child, ngram + [token])
        yield from _rec(self.root, [])

    def update_stats(self):
        """ Update the internal statistics (like entropy, and variance & means
        for the entropy variations. """
        if not self.dirty:
            return

        #"MATCH (r)-[:Child*0..]->(s) WHERE ID(r) = %i MATCH (s)-[:Child]->(c) SET s.entropy = log10(c.count / sum) / log10(2)

        tx = self.graph.cypher.begin()
        for s, in self.graph.cypher.stream("MATCH (r)-[:Child*0..]->(s) WHERE ID(r) = {root} RETURN ID(s)", {'root': self.root}):
            e = entropy(j[0] for j in self.graph.cypher.stream("MATCH (s)-[:Child]->(c) WHERE ID(s) = {pid} RETURN c.count", {'pid': s}))
            tx.append("MATCH (s) WHERE id(s) = {pid} SET s.entropy = {e}", {'pid': s, 'e': e})
        tx.commit()

        for i in range(self.depth):
            if i == 0:
                mean, stdev = self.graph.cypher.execute("MATCH (r)-[:Child]->(s) WHERE ID(r) = {root} RETURN avg(s.entropy - r.entropy), stdevp(s.entropy - r.entropy)", {'root': self.root})[0]
            else:
                q = 'MATCH (root)' + '-[:Child]->()' * (i - 1) + '-[:Child]->(r)-[:Child]->(s) WHERE ID(root) = {root}'
                mean, stdev = self.graph.cypher.execute(q + " RETURN avg(s.entropy - r.entropy), stdevp(s.entropy - r.entropy)", {'root': self.root})[0]
            assert mean is not None and stdev is not None
            self.normalization[i] = (mean, stdev)

        self.dirty = False

    def _check_dirty(self):
        if self.dirty:
            logging.warning("Updating the tree statistics (update_stats method), as we query it while dirty. This is a slow operation.")
            self.update_stats()

    def merge(self, other):
        tx = self.graph.cypher.begin()
        for ngram in other:
            count = other.query_node(ngram)[0]
            if count == 0:
                continue
            self.dirty = True

            d = {'t%i' % tid: str(token) for tid, token in enumerate(ngram)}
            d.update({'count': count, 'root': self.root})
            if ngram:
                d['tl'] = str(ngram[-1])

            if len(ngram) > 1:
                q = "(root)" + '()'.join("-[:Child {token: {t%i}}]->" % tid for tid, token in enumerate(ngram[:-1])) + "(parent) WHERE id(root) = {root}"
                tx.append('MATCH %s MERGE (parent)-[:Child {token: {tl}}]->(node) ON CREATE SET node.count = {count} ON MATCH SET node.count = node.count + {count}' % q, d)
            elif len(ngram) == 1:
                q = "(parent) WHERE id(parent) = {root}"
                tx.append('MATCH %s MERGE (parent)-[:Child {token: {tl}}]->(node) ON CREATE SET node.count = {count} ON MATCH SET node.count = node.count + {count}' % q, d)
            else:
                tx.append('MATCH (root) WHERE id(root) = {root} SET root.count = root.count + {count}', d)

            for docid, count in other.query_postings(ngram):
                q = "(root)" + '()'.join("-[:Child {token: {t%i}}]->" % tid for tid, token in enumerate(ngram)) + "(child) WHERE id(root) = {root}"
                d2 = d
                d2.update({'docid': docid})
                tx.append('MATCH %s MERGE (child)-[:Document {docid: {docid}}]->(node) ON CREATE SET node.count = {count} ON MATCH SET node.count = node.count + {count}' % q, d2)

        tx.commit()

    def add_ngram(self, ngram, docid, freq=1):
        """ Add a ngram to the tree.
        You can specify the number of times you add (or substract) that ngram by using the `freq` argument.
        """

        if len(ngram) > self.depth:
            raise ValueError("The size of the ngram parameter must be less or equal than depth ({})".format(self.depth))

        self.graph.cypher.run("MATCH (s) WHERE id(s) = {root} SET s.count = s.count + {count}", {'root': self.root, 'count': freq})

        self._add_ngram(self.root, ngram, docid, freq)

        self.dirty = True

    def _add_ngram(self, node, ngram, docid, freq):
        """ Recursive function used to add a ngram.
        """

        try:
            token = ngram[0]

        except IndexError:
            # reached end of ngram : add it to the postlist
            self.graph.cypher.run(
                "MATCH (s) WHERE id(s) = {nid} MERGE (s)-[:Document {docid: {docid}}]->(r) ON CREATE SET r.count = {count} ON MATCH SET r.count = r.count + {count}",
                {'nid': node, 'count': freq, 'docid': docid}
            )

        else:
            child = self.graph.cypher.execute_one(
                "MATCH (s) WHERE id(s) = {nid} MERGE (s)-[:Child {token: {token}}]->(c) ON CREATE SET c.count = {count} ON MATCH SET c.count = c.count + {count} RETURN id(c)",
                {'token': str(token), 'count': freq, 'nid': node}
            )
            # recurse, add the end of the ngram
            self._add_ngram(child, ngram[1:], docid, freq)
    
    def _query_node(self, ngram):
        """ Internal function that returns count, entropy and node_id """
        self._check_dirty()

        d = {'t%i' % tid: str(token) for tid, token in enumerate(ngram or [])}
        d.update({'root': self.root})

        if ngram:
            q = "(root)" + '()'.join("-[:Child {token: {t%i}}]->" % tid for tid, token in enumerate(ngram)) + "(leaf)"
            try:
                count, entropy, node_id = self.graph.cypher.execute("MATCH %s WHERE id(root) = {root} RETURN leaf.count, leaf.entropy, id(leaf)" % q, d)[0]
            except IndexError:
                return (0., 0., None)
        else:
            count, entropy, node_id = self.graph.cypher.execute("MATCH (root) WHERE id(root) = {root} RETURN root.count, root.entropy, id(root)", d)[0]

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
        for docid, count in self.graph.cypher.stream("MATCH (s)-[r:Document]->(l) WHERE id(s) = {nid} RETURN r.docid, s.count", {'nid': node_id}):
            yield (docid, count)

    def query_ev(self, ngram):
        """ Return the entropy variation for the ngram.
        """
        self._check_dirty()

        if not ngram:
            r = 0.

        elif len(ngram) == 1:
            r = self.graph.cypher.execute_one(
                "MATCH (root)-[R:Child {token: {token}}]->(c) WHERE id(root) = {root} RETURN c.entropy - root.entropy",
                {'root': self.root, 'token': str(ngram[0])}
            )
            if r is None:
                r = -self._query_node(None)[1]

        else:

            q = "(root)" + ''.join("-[:Child {token: {t%i}}]->(c%i)" % (tid, tid) for tid, token in enumerate(ngram))

            d = {'t%i' % tid: str(token) for tid, token in enumerate(ngram)}
            d.update({'root': self.root})

            r = self.graph.cypher.execute_one(
                "MATCH %s WHERE id(root) = {root} RETURN c%i.entropy - c%i.entropy" % (q, len(ngram) - 1, len(ngram) - 2),
                d
            )
            if r is None:
               r = -self._query_node(ngram[:-1])[1]

        return r

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
