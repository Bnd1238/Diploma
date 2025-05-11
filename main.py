#lon долгота/x
#lat широта/y
from neo4j import GraphDatabase
import osmiter
import json 
import math as math
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
map = osmiter.iter_from_osm("map.osm")

R=6372.795
INF=R

car=False   #наличие машины
summer=True #Время года
target=0    #Что минимизируется? 0-расстояние,1-время,2-деньги,3-комфорт
kids=False   #Наличие детей. Необходимый комфорт 5
home=5

transport={
    "car":{
        "speed":30,
        "price":0,
        "comfort":10
    },
    "bus":{
        "speed":20,
        "price":30,
        "comfort":8
    },
    "ferry":{
        "speed":10,
        "price":100,
        "comfort":2
    }

}
def Query(query,parameters):
    return driver.session().run(query,parameters)

def r(a, b):
    Ax=a[0]["a"]["lon"]
    Ay=a[0]["a"]["lat"]
    Bx=b[0]["a"]["lon"]
    By=b[0]["a"]["lat"]
    return math.sqrt( (Ax-Bx)**2+(Ay-By)**2)

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
        a=Query("""
        MATCH (a:Node {id:$a})
        RETURN (a) 
        """,{"a": way["nd"][i]}).data()
        b=Query("""
        MATCH (a:Node {id:$a})
        RETURN (a) 
        """,{"a": way["nd"][i+1]}).data()
        
        Query("""
        MATCH (a:Node {id:$a}),(b:Node{id:$b})
        CREATE (a)-[:Car]->(b),(b)-[:Car]->(a) 
        """,{"a": way["nd"][i],"b":way["nd"][i+1]})
        Query("""
        MATCH (a)-[r:Car]->(b)
        WHERE a.id = $a AND b.id = $b
        SET r.range = $r, r.id=$id, r.tag=$tag
        """,{"a": way["nd"][i],"b":way["nd"][i+1],"id":way["id"],"r":r(a,b),"tag":json.dumps(way["tag"])})
        Query("""
        MATCH (b)-[r:Car]->(a)
        WHERE a.id = $a AND b.id = $b
        SET r.range = $r, r.id=$id, r.tag=$tag
        """,{"a": way["nd"][i],"b":way["nd"][i+1],"id":way["id"],"r":r(a,b),"tag":json.dumps(way["tag"])})
def add_Rel(rel):
    nodes=[]
    #print(rel["tag"]["ref"])

    for member in rel["member"]:
        if member["type"]=="node" and member["role"]=="stop":
            nodes.append(member["ref"])
    for i in range(len(nodes)-1):
        a=Query("""
        MATCH (a:Node {id:$a})
        RETURN (a) 
        """,{"a": nodes[i]}).data()
        b=Query("""
        MATCH (a:Node {id:$a})
        RETURN (a) 
        """,{"a": nodes[i+1]}).data()

        Query("""
        MATCH (a:Node {id:$a}),(b:Node{id:$b})
        CREATE (a)-[:Public]->(b),(b)-[:Public]->(a) 
        """,{"a":nodes[i],"b":nodes[i+1]})
        Query("""
        MATCH (a)-[r:Public]->(b)
        WHERE a.id = $a AND b.id = $b
        SET r.range = $r, r.tag=$tag
        """,{"a":nodes[i],"b":nodes[i+1],"r":r(a,b),"tag":json.dumps(rel["tag"])})
        Query("""
        MATCH (b)-[r:Public]->(a)
        WHERE a.id = $a AND b.id = $b
        SET r.range = $r, r.tag=$tag
        """,{"a":nodes[i],"b":nodes[i+1],"r":r(a,b),"tag":json.dumps(rel["tag"])})
def migration():
    driver.session().run("""MATCH(n) detach delete (n)""")
    for node in map:
        if node["type"]=="node":
            add_Node(node)
        if node["type"]=="way":
            add_Way(node)
        if node["type"]=="relation":
            add_Rel(node)

def prep():
    print("У Вас есть машина? да/нет")
    ans=input()
    if ans=="да":
        car=True
    print("У Вас есть дети?")
    ans=input()
    if ans=="да":
        kids=True
    print("Что минимизировать? \n0-расстояние\n1-время\n2-расходы\n3-максимизировать комфорт")
    target=int(input())

def make_graph():
    V=Query("""MATCH (n:Node) RETURN n.id""",{}).data()

    Vertities={}
    for i in range(len(V)):
        Vertities[V[i]["n.id"]]=i
   
    Edges=Query("""MATCH (a)-[r]->(b) RETURN TYPE(r) AS type,startNode(r) AS a,r.tag AS tag,r.id AS id, endNode(r) AS b,r.range AS range""",{}).data()
    size=len(V)
    Graph=["INF"]*size
    for i in range(size):
        Graph[i]=["INF"]*size
    for i in range(size):
        Graph[i][i]=0
    
    for i in Edges:
        a=i["a"]
        b=i["b"]
        id=i["id"]
        tag=i["tag"]
        r=i["range"]
        type=i["type"]
        Graph[Vertities[a["id"]]][Vertities[b["id"]]]=r
    print(Graph)
migration()
make_graph()
driver.close()
