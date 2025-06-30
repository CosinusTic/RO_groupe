import os, pickle, networkx as nx, pandas as pd
rows=[]
for slug in os.listdir("resources/"):
    ndir=f"resources/"+slug
    try:
        G_un=pickle.load(open(ndir+"/eulerized_graph.pkl","rb"))
        G_or=pickle.load(open(ndir+"/eulerized_graph_oriented.pkl","rb"))
    except FileNotFoundError:
        continue
    one_way=sum(1 for u,v in G_or.edges() if not G_or.has_edge(v,u))
    rows.append(dict(borough=slug,
                     undirected=len(G_un.edges()),
                     directed=len(G_or.edges()),
                     one_way=one_way))
print(pd.DataFrame(rows))

