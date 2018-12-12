import neo4j

f = open('mzk_data.txt')
data = f.readlines()
f.close()

data = [l.strip() for l in data]
sep_idx = data.index('=====')

transp_data = {}

while True:
    line_data = data[:sep_idx]
    data = data[sep_idx+1:]

    bus_no = line_data[0]

    split_idx = line_data.index('-----')
    route = line_data[1:split_idx]
    route = [l.split(' : ') for l in route]

    time_table = line_data[split_idx+1:]
    time_table = [l.split(' : ') for l in time_table]

    if len(data) == 0: break

    sep_idx = data.index('=====')

    transp_data[bus_no] = (time_table, route)


driver = neo4j.GraphDatabase().driver('bolt://localhost:7687', auth=('neo4j', 'dupablada'))
#%%

stops = set()
connected_stops = {}
for bus_no, (time_table, route) in transp_data.iteritems():
    for time, stop in route:
        stops.add(stop)

    for stop_from, stop_to in zip(route[1:], route[:-1]):
        sf, st = min(stop_from[1], stop_to[1]), max(stop_from[1], stop_to[1])
        connected_stops[sf, st] =  int(stop_from[0]) - int(stop_to[0])


#%%

def create_stops(tx, all_stops):
    for stop in all_stops:
        q = "CREATE (n:STOP {name:'%s'})" % stop
        tx.run(q)

def create_connections(tx, connected_stops):
    for (stop_from, stop_to), time in connected_stops.iteritems():
        q = ("MATCH (a:STOP{name:'%s'}),(b:STOP{name:'%s'})"  % (stop_from, stop_to)) \
                + " MERGE (a)-[:CONNECTED{time:%s}]-(b) " % time
        tx.run(q)

def create_buses(tx, transp_data):
    for bus_no, data in transp_data.iteritems():
        q = "CREATE (:BUS{line:'%s'})" % bus_no
        tx.run(q)
        for minutes, stop_name in data[1]:
            q = ("MATCH (b:BUS{line:'%s'}), (s:STOP{name:'%s'})" % (bus_no, stop_name)) \
                + " CREATE (b)-[:STOPS_AT]->(s)"
            tx.run(q)


with driver.session() as session:
    session.write_transaction(create_stops, stops)
    session.write_transaction(create_connections, connected_stops)
    session.write_transaction(create_buses, transp_data)

#%%
with driver.session() as session:
    session.write_transaction(lambda tx: tx.run('MATCH (n) DETACH DELETE n'))
