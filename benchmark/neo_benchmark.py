import datetime
from py2neo import Graph


def bench(query, count, reset=True):
    graph = Graph()

    if reset:
        graph.cypher.run("MATCH (n) OPTIONAL MATCH (n)-[r]-() DELETE n,r")
        graph.cypher.run(
            "CREATE CONSTRAINT ON (node:Node) ASSERT node.number IS UNIQUE"
        )
        graph.cypher.run("CREATE (r:Root)")

    start = datetime.datetime.now()
    tx = graph.cypher.begin()
    for i in range(count):
        tx.append(query, {"i": i})
    tx.commit()

    print("---")
    print("query : %s" % query)
    print(
        "%i create. %s/second."
        % (count, count // (datetime.datetime.now() - start).total_seconds())
    )


if __name__ == "__main__":
    bench("MATCH (:Root)-[:Child]->(n:Node {number: {i}}) RETURN n.count", 1000)
    bench("CREATE (:Root)-[:Child]->(:Node {number: {i}, count: 1})", 1000)
    bench(
        "MATCH (root:Root) CREATE (root)-[:Child]->(:Node {number: {i}, count: 1})",
        1000,
    )
    bench(
        "MATCH (root:Root) MERGE (root)-[:Child]->(n:Node {number: {i}}) ON CREATE SET n.count = 1 ON MATCH SET n.count = n.count + 1",
        1000,
    )
    bench(
        "MATCH (root:Root)-[:Child]->(n:Node {number: {i}}) SET n.count = n.count + 1",
        1000,
    )
    bench(
        "MATCH (root:Root) CREATE UNIQUE (root)-[:Child]->(n:Node {number: {i}}) SET n.count = coalesce(n.count, 0) + 1",
        1000,
    )
    bench(
        "MATCH (root:Root) MERGE (n:Node {number: {i}}) ON CREATE SET n.count = 1 ON MATCH SET n.count = n.count + 1 MERGE (root)-[:Child]->(n)"
    )
