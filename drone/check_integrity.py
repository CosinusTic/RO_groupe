import os, pickle, pandas as pd

ROOT = "resources"
rows = []

for slug in os.listdir(ROOT):
    folder = os.path.join(ROOT, slug)
    if not os.path.isdir(folder):               # <-- skip files (html, png…)
        continue

    g_un = os.path.join(folder, "eulerized_graph.pkl")
    g_or = os.path.join(folder, "eulerized_graph_oriented.pkl")
    if not (os.path.isfile(g_un) and os.path.isfile(g_or)):   # <-- only real boroughs
        continue

    G_un = pickle.load(open(g_un, "rb"))
    G_or = pickle.load(open(g_or, "rb"))
    one_way = sum(
        1 for u, v in G_or.edges() if not G_or.has_edge(v, u)
    )
    rows.append({
        "borough": slug,
        "undirected": len(G_un.edges()),
        "directed": len(G_or.edges()),
        "one_way": one_way
    })

print(pd.DataFrame(rows))

