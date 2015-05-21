from __future__ import division
import logging
from py2neo import Graph
import random
import sys

from eleve.storage import Storage
from eleve.memory import entropy

from py2neo.packages.httpstream import http
http.socket_timeout = 9999

logger = logging.getLogger(__name__)

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
            r = self.graph.cypher.stream("MATCH (s)-[r:Child]->(c) WHERE id(s) = {nid} RETURN r.token, ID(c), c.count", {'nid': node})
            for token, child, count in r:
                yield (ngram + [token], count)
                yield from _rec(child, count, ngram + [token])
        yield ([], self._query_node(None)[0])
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
            logger.warning("Updating the tree statistics (update_stats method), as we query it while dirty. This is a slow operation.")
            self.update_stats()

    def merge(self, other):
        tx = self.graph.cypher.begin()
        for ngram, count in other:
            if count == 0:
                continue
            self.dirty = True

            #ngram = [self.gid + ','.join(map(str, ngram[:i+1])) for i in range(len(ngram))] ###FIXME

            d = {'t%i' % tid: str(token) for tid, token in enumerate(ngram)}
            d.update({'count': count})

            if len(ngram) > 1:
                q = "(:Root%s)" % self.gid + ''.join("-[:Child]->(n%i:Node {token: {t%i}})" % (tid, tid) for tid, token in enumerate(ngram[:-1]))
                tx.append('MATCH %s MERGE (n%i)-[:Child]->(node:Node {token: {t%i}}) ON CREATE SET node.count = {count} ON MATCH SET node.count = node.count + {count}' % (q, len(ngram) - 2, len(ngram) - 1), d)
            elif len(ngram) == 1:
                tx.append('MATCH (root:Root%s) MERGE (root)-[:Child]->(node:Node {token: {t0}}) ON CREATE SET node.count = {count} ON MATCH SET node.count = node.count + {count}' % self.gid, d)
            else:
                tx.append('MATCH (root:Root%s) SET root.count = root.count + {count}' % self.gid, d)

            for docid, count in other.query_postings(ngram):
                q = "(:Root%s)" % self.gid + ''.join("-[:Child]->(n%i {token: {t%i}})" % (tid, tid) for tid, token in enumerate(ngram))
                d2 = d
                d2.update({'docid': docid})
                tx.append('MATCH %s MERGE (t%i)-[:Document]->(node {docid: {docid}}) ON CREATE SET node.count = {count} ON MATCH SET node.count = node.count + {count}' % (q, len(ngram) - 1), d2)

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
                "MATCH (s) WHERE id(s) = {nid} MERGE (s)-[:Document]->(r {docid: {docid}}) ON CREATE SET r.count = {count} ON MATCH SET r.count = r.count + {count}",
                {'nid': node, 'count': freq, 'docid': docid}
            )

        else:
            child = self.graph.cypher.execute_one(
                "MATCH (s) WHERE id(s) = {nid} MERGE (s)-[:Child]->(c {token: {token}}) ON CREATE SET c.count = {count} ON MATCH SET c.count = c.count + {count} RETURN id(c)",
                {'token': str(token), 'count': freq, 'nid': node}
            )
            # recurse, add the end of the ngram
            self._add_ngram(child, ngram[1:], docid, freq)
    
    def _query_node(self, ngram):
        """ Internal function that returns count, entropy and node_id """
        self._check_dirty()

        d = {'t%i' % tid: str(token) for tid, token in enumerate(ngram or [])}

        if ngram:
            q = "(:Root%s)" % self.gid + ''.join("-[:Child]->(n%i {token: {t%i}})" % (tid, tid) for tid, token in enumerate(ngram))
            try:
                count, entropy, node_id = self.graph.cypher.execute("MATCH %s RETURN n%i.count, n%i.entropy, id(n%i)" % (q, len(ngram) - 1, len(ngram) - 1, len(ngram) - 1), d)[0]
            except IndexError:
                return (0., 0., None)
        else:
            count, entropy, node_id = self.graph.cypher.execute("MATCH (root:Root%s) RETURN root.count, root.entropy, id(root)" % self.gid, d)[0]

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
            #ngram = [self.gid + ','.join(map(str, ngram[:i+1])) for i in range(len(ngram))] ###FIXME
            r = self.graph.cypher.execute_one(
                "MATCH (root:Root%s)-[:Child]->(c {token: {token}}) RETURN c.entropy - root.entropy" % self.gid,
                {'token': str(ngram[0])}
            )
            if r is None:
                r = -self._query_node(None)[1]

        else:
            #ngram = [self.gid + ','.join(map(str, ngram[:i+1])) for i in range(len(ngram))] ###FIXME

            q = "(:Root%s)" % self.gid + ''.join("-[:Child]->(c%i {token: {t%i}})" % (tid, tid) for tid, token in enumerate(ngram))

            d = {'t%i' % tid: str(token) for tid, token in enumerate(ngram)}

            r = self.graph.cypher.execute_one(
                "MATCH %s RETURN c%i.entropy - c%i.entropy" % (q, len(ngram) - 1, len(ngram) - 2),
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
