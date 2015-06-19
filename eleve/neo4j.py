from __future__ import division
import logging
import random
import warnings
import sys
import math

from eleve.storage import Storage
from eleve.memory import entropy

from py2neo import Graph
from py2neo.packages.httpstream import http
http.socket_timeout = 9999

logger = logging.getLogger(__name__)

class Neo4jStorage(Storage):
    """ Neo4j storage.

    This storage use a neo4j database. It store tries, starting from a root node.
    The root node have the label `RootGID` where GID is the "name" of the trie.

    All nodes have an attribute entropy.
    All nodes (except from root) have the label :Node, and an attribute `path` which is
    GID->token1->token2->...->node_token. Where node token is the token of this node.
    We store the full path instead of the token for performance reasons, because it allows
    us to have an index on the path parameter that speeds up queries a lot.

    """

    def __init__(self, depth, gid=None):
        """
        :param depth: Maximum length of stored ngrams
        :param gid: The ID of the root node in the neo4j database (to load existing trees, and have multiple ones in the database)
        """
        self.depth = depth
        self.graph = Graph()
        self.gid = str(gid if gid is not None else random.randint(0,1000000000))
        self.load_root()

    def _path(self, ngram):
        return self.gid + ''.join('->%s' % token for token in ngram)

    def load_root(self):
        try:
            self.root, self.dirty = self.graph.cypher.execute("MATCH (r:RootNode:Root%s) RETURN ID(r), r.dirty" % self.gid)[0]
        except IndexError:
            self.root = self.graph.cypher.execute_one("CREATE (r:RootNode:Root%s {count: 0, depth: %i}) RETURN ID(r)" % (self.gid, self.depth))
            self.graph.cypher.run("CREATE CONSTRAINT ON (node:Node) ASSERT node.path IS UNIQUE")
            self.dirty = True
        assert isinstance(self.root, int)

    def clear(self):
        # delete everything
        tx = self.graph.cypher.begin()
        tx.append("MATCH (:RootNode:Root%s)-[r*]->(n) delete last(r),n" % self.gid)
        tx.append("MATCH (n:RootNode:Root%s) delete n" % self.gid)
        tx.commit()
        self.load_root()
        return self

    def update_stats(self):
        """ Update the internal statistics (like entropy, and variance & means
        for the entropy variations. """
        if not self.dirty:
            return

        self.normalization = [(0,0,0)] * self.depth

        tx = self.graph.cypher.begin()
        set_count = 0

        def _rec(parent_entropy, node_id, level):
            nonlocal set_count
            counts = []
            for path, count in self.graph.cypher.stream("MATCH (n)-[:Child]->(c) WHERE ID(n) = {pid} RETURN c.path, c.count", {'pid': node_id}):
                if path.split('->')[-1] == 'None':
                    counts.extend(1 for _ in range(count))
                else:
                    counts.append(count)
            e = entropy(counts) if counts else -1 # -1 means that it's a leaf

            tx.append("MATCH (n) WHERE ID(n) = {pid} SET n.entropy = {e}", {'pid': node_id, 'e': e})
            if set_count > 10000:
                tx.process()
                set_count = 0
            else:
                set_count += 1

            if not counts:
                return

            if parent_entropy is not None and (e != 0 or parent_entropy != 0):
                # update the normalization factor
                ve = e - parent_entropy
                a, q, k = self.normalization[level]
                k += 1
                old_a = a
                a += (ve - a) / k
                q += (ve - old_a)*(ve - a)
                self.normalization[level] = (a, q, k)

            for s, in self.graph.cypher.stream("MATCH (n)-[:Child]->(c) WHERE ID(n) = {pid} RETURN ID(c)", {'pid': node_id}):
                _rec(e, s, level + 1)

        _rec(None, self.root, -1)

        tx.commit()

        self.normalization = [(a, math.sqrt(q / (k or 1.))) for a, q, k in self.normalization]

        self.graph.cypher.run("MATCH (r:Root%s) SET r.dirty = FALSE" % self.gid)
        self.dirty = False

    def _check_dirty(self):
        if self.dirty:
            logger.warning("Updating the tree statistics (update_stats method), as we query it while dirty. This is a slow operation.")
            self.update_stats()

    def merge(self, other):
        has_count = lambda ngram_count: ngram_count[1] != 0

        tx = self.graph.cypher.begin()
        for ngram, count in filter(has_count, other):
            if ngram:
                tx.append('MATCH (n:Node {path: {p}}) RETURN n.count', {'p': self._path(ngram)})
            else:
                tx.append('MATCH (n:Root%s) RETURN n.count' % self.gid)
        
        tx2 = self.graph.cypher.begin()
        for (ngram, count), old_count in zip(filter(has_count, other), tx.commit()):
            old_count = old_count[0][0] if old_count else None

            d = {'c': count if old_count is None else count + old_count,
                 'p': self._path(ngram) if ngram else None}

            if old_count is None:
                if len(ngram) > 1:
                    d['lp'] = self._path(ngram[:-1])
                    tx2.append('MATCH (p:Node {path: {lp}}) CREATE (p)-[:Child]->(:Node {path: {p}, count: {c}})', d)
                else:
                    # create a child of the root
                    tx2.append('MATCH (r:Root%s) CREATE (r)-[:Child]->(:Node {path: {p}, count: {c}})' % self.gid, d)
            else:
                if len(ngram) > 0:
                    tx2.append('MATCH (n:Node {path: {p}}) SET n.count = {c}', d)
                else:
                    tx2.append('MATCH (r:Root%s) SET r.count = {c}, r.dirty = TRUE' % self.gid, d)

            self.dirty = True

        tx2.commit()

        # TODO: POSTINGS
        """
        for docid, count in other.query_postings(ngram):
            q = "(:Root%s)" % self.gid + ''.join("-[:Child]->(n%i {token: {t%i}})" % (tid, tid) for tid, token in enumerate(ngram))
            d2 = d
            d2.update({'docid': docid})
            tx.append('MATCH %s MERGE (t%i)-[:Document]->(node {docid: {docid}}) ON CREATE SET node.count = {count} ON MATCH SET node.count = node.count + {count}' % (q, len(ngram) - 1), d2)
        """

    def add_ngram(self, ngram, docid, freq=1):
        """ Add a ngram to the tree.
        You can specify the number of times you add (or substract) that ngram by using the `freq` argument.
        """

        warnings.warn("The performance of adding individual ngrams with Neo4j is horrible. You should use an intermediate storage that will do `merge`.")

        ngram = list(map(str, ngram))
        fake_tree = [(ngram[:i], freq) for i in range(len(ngram) + 1)]
        self.merge(fake_tree)
    
    def query_node(self, ngram):
        """ Return a tuple with the main node data : (count, entropy).
        Count is the number of ngrams starting with the ``ngram`` parameter, entropy the entropy after the ngram.
        """
        self._check_dirty()

        if ngram:
            r = self.graph.cypher.execute(
                "MATCH (n:Node {path: {p}}) RETURN n.count, n.entropy", 
                {'p': self._path(ngram)}
            )
        else:
            r = self.graph.cypher.execute("MATCH (n:Root%s) RETURN n.count, n.entropy" % self.gid)

        if r:
            count, entropy = r[0]
            return (count, entropy if entropy != -1 else None)
        return (0, None)

    def query_postings(self, ngram):
        raise NotImplementedError()

        # TODO: Postings.
        """
        node_id = self._query_node(ngram)
        if node_id is None:
            return
        for docid, count in self.graph.cypher.stream("MATCH (s)-[r:Document]->(l) WHERE id(s) = {nid} RETURN r.docid, s.count", {'nid': node_id}):
            yield (docid, count)
        """

    def query_ev(self, ngram):
        """ Return the entropy variation for the ngram.
        """
        self._check_dirty()

        if not ngram:
            return None

        if len(ngram) == 1:
            r = self.graph.cypher.execute(
                "MATCH (root:Root%s), (c:Node {path: {p}}) RETURN c.entropy, root.entropy" % self.gid,
                {'p': self._path(ngram)}
            )
        else:
            r = self.graph.cypher.execute(
                "MATCH (c:Node {path: {pc}}), (p: Node {path: {pp}}) RETURN c.entropy, p.entropy",
                {'pc': self._path(ngram), 'pp': self._path(ngram[:-1])}
            )

        if r:
            child, parent = r[0]
            assert parent != -1
            if child != -1 and (child != 0 or parent != 0):
                return child - parent
        return None

    def query_autonomy(self, ngram, z_score=True):
        """ Return the autonomy (normalized entropy variation) for the ngram.
        """
        if not ngram:
            raise ValueError("Can't query the autonomy of the root node.")
        self._check_dirty()
        mean, variance = self.normalization[len(ngram) - 1]
        ev = self.query_ev(ngram)
        if ev is None:
            return -100. # FIXME
        nev = ev - mean
        if z_score:
            nev /= variance
        return nev
