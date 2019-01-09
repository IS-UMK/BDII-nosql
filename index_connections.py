import neo4j

driver = neo4j.GraphDatabase().driver('bolt://0.0.0.0:7687', auth=('neo4j', 'dupablada'))

def get_stops(tx):
    q = "MATCH (n:STOP) RETURN n;"
    return tx.run(q)
    
def get_connections(tx, f, t):
    q = "MATCH (f:STOP{name:'%s'}), (t:STOP{name:'%s'})" %(f,t) \
        + " WITH f,t" \
        + " MATCH path = allShortestPaths((f)-[:STOPS_AT*..20]-(t))" \
        + " RETURN path;" 
    return tx.run(q)

with driver.session() as session:
    stops = session.read_transaction(get_stops)    
    stops = list(stops)
stops = [s['n']['name'] for s in list(stops)]
with driver.session() as session:
    for f in stops:
        for t in stops:
            if f ==t : continue
            connections = session.read_transaction(get_connections,f,t)    
            connections = list(connections)
            print "============"
            print connections
    
    
