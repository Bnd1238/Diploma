#lon долгота
#lat широта
from neo4j import GraphDatabase
import osmiter
import json 
R=6372.795
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
map = osmiter.iter_from_osm("map.osm")
def Query(query,parameters):
    return driver.session().run(query,parameters)
def r():#пока просто заглушка
    '''Alon=a["lon"]
    Alat=a["lat"]
    Blon=b["lon"]
    Blat=b["lat"]'''
    Alat=59.81716
    Alon=30.30568
    Blat=59.87162
    Blon=30.31367
    return 5
    #return 2*math.asin(math.sqrt(math.sin((Alat-Blat))**2+math.cos(Alat)*math.cos(Blat)*math.sin((Alon-Blon)/2)**2))
def add_Node(node):
    params={
        "id": node["id"],
        "lat": node["lat"], 
        "lon": node["lon"],
        "tag": json.dumps(node["tag"])
    }
    query="""
    CREATE (n:Node { 
        id: $id,
        lat: $lat,
        lon: $lon,
        tag: $tag
    })
    """
    driver.session().run(query,params).single()
    
def add_Way(way):
    for i in range(len(way["nd"])-1):
        coast=r()
        Query("""
        MATCH (a:Node {id:$a}),(b:Node{id:$b})
        CREATE (a)-[:car]->(b),(b)-[:car]->(a) 
        """,{"a": way["nd"][i],"b":way["nd"][i+1]})
        Query("""
        MATCH (a)-[r:car]->(b)
        WHERE a.id = $a AND b.id = $b
        SET r.coast = $r, r.id=$id
        """,{"a": way["nd"][i],"b":way["nd"][i+1],"id":way["id"],"r":r()})
        Query("""
        MATCH (b)-[r:car]->(a)
        WHERE a.id = $a AND b.id = $b
        SET r.coast = $r, r.id=$id
        """,{"a": way["nd"][i],"b":way["nd"][i+1],"id":way["id"],"r":r()})
def add_Rel(rel):
    nodes=[]
    #print(rel["tag"]["ref"])
    for member in rel["member"]:
        if member["type"]=="node" and member["role"]=="stop":
            nodes.append(member["ref"])
    print(nodes)
    for i in range(len(nodes)-1):
        Query("""
        MATCH (a:Node {id:$a}),(b:Node{id:$b})
        CREATE (a)-[:bus]->(b),(b)-[:bus]->(a) 
        """,{"a":nodes[i],"b":nodes[i+1]})
        Query("""
        MATCH (a)-[r:bus]->(b)
        WHERE a.id = $a AND b.id = $b
        SET r.price = $r, r.route=$route
        """,{"a":nodes[i],"b":nodes[i+1],"r":r(),"route":rel["tag"]["ref"]})
        Query("""
        MATCH (b)-[r:bus]->(a)
        WHERE a.id = $a AND b.id = $b
        SET r.price = $r, r.route=$route
        """,{"a":nodes[i],"b":nodes[i+1],"r":r(),"route":rel["tag"]["ref"]})
def migration():
    for node in map:
        print(node["type"])
        if node["type"]=="node":
            add_Node(node)
        if node["type"]=="way":
            add_Way(node)
        if node["type"]=="relation":
            add_Rel(node)
migration()
driver.close()
