#lon долгота/x
#lat широта/y
from neo4j import GraphDatabase
import osmiter
import json 
import math as math
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"),max_connection_pool_size=100)
map = osmiter.iter_from_osm("map.osm")

INF=999999

discomfort=10
trip=[]

Input={
    "target":0,# 0-расстояние,1-время,2- максимизация комфорта
    "car":False,
    "season":"summer",
    "seasickness":False,
    "home":5
}  
ans={"best":INF,"bestway":[],"start":Input["home"],"counter":0,"no":0,"type":"public"}
transport={
    "car":{
        "speed":10,
        "comfort":1
    },
    "bus":{
        "speed":5,
        "comfort":3
    },
    "ferry":{
        "speed":1,
        "comfort":10
    }

}
def Query(query, parameters):

    with driver.session() as session:
        result = session.run(query, parameters).data()
    return result
def r(a, b):
    return (a[0]["a"]["id"]+b[0]["a"]["id"])%5+1

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
        """,{"a": way["nd"][i]})
        b=Query("""
        MATCH (a:Node {id:$a})
        RETURN (a) 
        """,{"a": way["nd"][i+1]})
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
    for member in rel["member"]:
        if member["type"]=="node" and member["role"]=="stop":
            nodes.append(member["ref"])
    for i in range(len(nodes)-1):
        a=Query("""
        MATCH (a:Node {id:$a})
        RETURN (a) 
        """,{"a": nodes[i]})
        b=Query("""
        MATCH (a:Node {id:$a})
        RETURN (a) 
        """,{"a": nodes[i+1]})

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
    global trip
    print("У Вас есть машина? да/нет")
    ans=input()
    if ans=="да":
        Input["car"]=True

    print("У Вас есть морская болезнь? да/нет")
    ans=input()
    if ans=="да":
        Input["seasickness"]=True
    print("Что минимизировать? \n0-расстояние\n1-время\n2-дискомфорт")
    Input["target"]=int(input())

    print("Сейчас летний период? да/нет")
    ans=input()
    
    if ans=="нет":
        Input["season"]="winter"

    print("укажите домашнюю точку")
    Input["home"]=int(input())
    trip.append(Input["home"])
    print("укажите точки интереса")
    points = [int(x) for x in input().split()]
    trip+=points
def coast(Graph,way):
    ans=0
    current=way[0]
    for i in range(1,len(way)):
        ans+=Graph[current][way[i]]["range"]
        current=way[i]
    return ans
def make_graph():
    global ans
    V=Query("""MATCH (n:Node) RETURN n.id""",{})
    Edges=Query("""MATCH (a)-[r]->(b) RETURN TYPE(r) AS type,startNode(r).id AS a,r.tag AS tag,r.id AS id, endNode(r).id AS b,r.range AS range""",{})
    size=len(V)
    GraphC=[-1]*size
    GraphP=[-1]*size
    for i in range(size):
        GraphC[i]=[-1]*size
        GraphP[i]=[-1]*size
    for i in range(size):
        GraphC[i][i]=0
        GraphP[i][i]=0
    old_ref=""
    for edge in Edges:
        if edge["type"]=="Public":
            tags=json.loads(edge["tag"])
            current_ref=tags["ref"]
            if tags["route"]=="ferry" and Input["seasickness"]:
                continue
            if "season" in tags:
                if tags["season"]!=Input["season"]:
                    continue
            if Input["target"]==0:
                GraphP[edge["a"]][edge["b"]]=edge["range"]
            elif Input["target"]==1:
                GraphP[edge["a"]][edge["b"]]=edge["range"]/transport[tags["route"]]["speed"]
                if current_ref!=old_ref:
                    GraphP[edge["a"]][edge["b"]]+=1/transport[tags["route"]]["speed"]
                    old_ref=current_ref
            elif Input["target"]==2:
                GraphP[edge["a"]][edge["b"]]=edge["range"]/transport[tags["route"]]["speed"]*transport[tags["route"]]["comfort"]
                if current_ref!=old_ref:
                    GraphP[edge["a"]][edge["b"]]+=discomfort
                    old_ref=current_ref
    if Input["car"]:
        for edge in Edges:
            if edge["type"]=="Car":
                if edge["tag"]!=None:
                    tags=json.loads(edge["tag"])
                    if "season" in tags:
                        if tags["season"]!=Input["season"]:
                            continue
                if Input["target"]==0:
                    GraphC[edge["a"]][edge["b"]]=edge["range"]
                elif Input["target"]==1:
                    GraphC[edge["a"]][edge["b"]]=edge["range"]/transport["car"]["speed"]
                elif Input["target"]==2:
                    GraphC[edge["a"]][edge["b"]]=edge["range"]/transport["car"]["speed"]*transport["car"]["comfort"]
    FullGraphP=[]
    FullGraphC=[]
    for i in range(size):
        FullGraphP.append(Dijkstra(GraphP,i))
    if Input["car"]:
        for i in range(size):
            FullGraphC.append(Dijkstra(GraphC,i))
    SalesmanC=[]
    SalesmanP=[]

    for i in (trip):
        nodeP=[]
        for j in trip:
            nodeP.append(FullGraphP[i][j]["range"])
        SalesmanP.append(nodeP)

    outHome=SalesmanP[0]
    toHome=[]
    for i in range(len(SalesmanP)):
        toHome.append(SalesmanP[i][0])
    if Input["car"]:
        for i in (trip):
            nodeC=[]
            for j in trip:
                nodeC.append(FullGraphC[i][j]["range"])
            SalesmanC.append(nodeC)
    vertitites=[]
    for i in range(len(trip)):
        vertitites.append(i)
    dfs(SalesmanP,0,[],vertitites,0,toHome,outHome)
    ansP=ans.copy()
    ans["best"]=INF
    if Input["car"]:
        outHome=SalesmanC[0]
        toHome=[]
        for i in range(len(SalesmanC)):
            toHome.append(SalesmanC[i][0])
        dfs(SalesmanC,0,[],vertitites,0,toHome,outHome)
    type="Car"
    FullGraph=FullGraphC
    if ansP["best"]<ans["best"]:
        type="Public"
        ans=ansP
        FullGraph=FullGraphP
    way=[]
    ans["type"]=type
    for i in ans["bestway"]:
        way.append(trip[i])
    print("path:",path(FullGraph,way))
    print("price:",coast(FullGraph,path(FullGraph,way)))
    print("type:",type)
    return

def dfs(Graph,node,way,V,mark,toHome,outHome):

    if mark>=ans["best"]:
        ans["counter"]+=1
        if V:
            ans["no"]+=1
        return
    if not V:
        if outHome[way[0]]+mark+toHome[way[-1]]:
            ans["best"]=outHome[way[0]]+mark+toHome[way[-1]]
            ans["bestway"]=way
            ans["counter"]+=1
            return
    for v in V:
        clone=V.copy()
        newway=way.copy()
        newway.append(v)
        clone.remove(v)
        dfs(Graph,v,newway,clone,mark+Graph[node][v],toHome,outHome)
def path(Graph,nodes):
    Way=[]
    current=int(Input["home"])
    nodes.append(current)
    for i in range(len(nodes)):
        Ans=[]
        ways=Graph[current][nodes[i]]
        parent=ways["parent"]
        while parent!=-1:
            Ans.append(parent)
            parent=Graph[current][parent]["parent"]
        current=nodes[i]
        Way+=Ans[::-1]
    Way.append(nodes[-1]) 
    return Way
def minimal(vertities):
    index=None
    mn=INF
    for i in range(len(vertities)):
        if not vertities[i]["used"]:
            if vertities[i]["range"]>-1:
                if vertities[i]["range"]<mn:
                    index=i
                    mn=vertities[i]["range"]
                    

    return index
def Dijkstra(graph,start):
    size=len(graph)
    verities=[]
    for i in range(size):
        verities.append({"range":-1,"parent":None,"used":False})
    verities[start]["range"]=0
    verities[start]["parent"]=-1
    for i in range(size):
        current=minimal(verities)
        if current==None:
            return verities
        verities[current]["used"]=True
        for j in range(size):
            if graph[current][j]>0:
                if verities[j]["range"]>verities[current]["range"]+graph[current][j] or verities[j]["range"]<0:
                    verities[j]["range"]=verities[current]["range"]+graph[current][j]
                    verities[j]["parent"]=current
    for i in range(size):
        verities[i]["used"]=False
    return verities
migration()
prep()
make_graph()
driver.close()
