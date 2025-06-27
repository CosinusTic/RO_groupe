#!/usr/bin/env python3
"""
Create directed-legal Eulerian walks for five Montréal boroughs.

Outputs per borough:
    raw_graph_oriented.pkl
    eulerized_graph_oriented.pkl   (directed!)
    eulerian_path_oriented.json
    path_visualization_oriented.png   (quick diagnostic)
"""
import os, json, pickle, math
import networkx as nx, osmnx as ox, matplotlib.pyplot as plt
from concurrent.futures import ThreadPoolExecutor
from slugify import slugify

BOROUGHS = [
    "Plateau-Mont-Royal, Montréal, Québec, Canada",
    "Outremont, Montréal, Québec, Canada",
    "Verdun, Montréal, Québec, Canada",
    "Anjou, Montréal, Québec, Canada",
    "Rivière-des-Prairies–Pointe-aux-Trembles, Montréal, Québec, Canada",
]
OUT_ROOT = "resources/neighborhoods"
os.makedirs(OUT_ROOT, exist_ok=True)

# -------------------------------------------------------------------------
def orient_eulerized_graph(G_dir, G_eu_un):
    """
    Build a directed MultiDiGraph whose edge set equals G_eu_un but
    respects the one-way directions in G_dir.  When both directions
    exist we keep both; when only one legal direction exists we keep it;
    if neither direction exists (rare after simplification) we fall back
    to the original u→v.
    """
    G = nx.MultiDiGraph()
    G.add_nodes_from(G_dir.nodes(data=True))

    for u, v in G_eu_un.edges():
        if G_dir.has_edge(u, v):
            for k, data in G_dir[u][v].items():
                G.add_edge(u, v, **data)
        elif G_dir.has_edge(v, u):          # one-way opposite
            for k, data in G_dir[v][u].items():
                G.add_edge(v, u, **data)
        else:
            # edge disappeared during simplification – add simple u→v
            G.add_edge(u, v, length=G_eu_un[u][v].get("length", 1))
    return G
# -------------------------------------------------------------------------
def directed_walk(G_dir, circuit):
    """
    Convert the undirected Eulerian circuit into a legal directed walk by
    replacing illegal (u,v) steps with a shortest legal path in G_dir.
    """
    walk = []
    for u, v in circuit:
        if G_dir.has_edge(u, v):
            walk.append((u, v))
        else:                              # need legal substitute
            try:
                sp = nx.shortest_path(G_dir, u, v, weight="length")
                walk.extend([(sp[i], sp[i+1]) for i in range(len(sp)-1)])
            except nx.NetworkXNoPath:
                # fall back to illegal edge (should be rare)
                walk.append((u, v))
    return walk
# -------------------------------------------------------------------------
def process(place):
    slug = slugify(place.split(",")[0])
    outdir = os.path.join(OUT_ROOT, slug)
    os.makedirs(outdir, exist_ok=True)
    print(f"[{slug}] downloading directed graph …")
    G_dir = ox.graph_from_place(place, network_type="drive",
                                simplify=True, retain_all=False)
    pickle.dump(G_dir, open(f"{outdir}/raw_graph_oriented.pkl", "wb"))

    # 1. undirected Eulerisation
    G_eu_un = nx.eulerize(G_dir.to_undirected())
    # 2. re-orient every edge back into legal directions
    G_eu_dir = orient_eulerized_graph(G_dir, G_eu_un)
    pickle.dump(G_eu_dir, open(f"{outdir}/eulerized_graph_oriented.pkl", "wb"))

    # 3. build directed walk
    circuit = list(nx.eulerian_circuit(G_eu_un))
    walk = directed_walk(G_dir, circuit)
    json.dump([{"u": u, "v": v} for u, v in walk],
              open(f"{outdir}/eulerian_path_oriented.json", "w"), indent=2)

    # 4. small diagnostic plot
    fig, ax = ox.plot_graph(G_dir, show=False, close=False,
                            edge_color="lightgray", node_size=0, bgcolor="white")
    xs, ys = [], []
    for u, v in walk:
        xs += [G_dir.nodes[u]["x"], G_dir.nodes[v]["x"]]
        ys += [G_dir.nodes[u]["y"], G_dir.nodes[v]["y"]]
    ax.plot(xs, ys, color="red", linewidth=1, alpha=0.7)
    plt.savefig(f"{outdir}/path_visualization_oriented.png", dpi=300)
    plt.close(fig)
    print(f"[{slug}] ✔ saved oriented graph & walk ({len(walk)} segments)")
# -------------------------------------------------------------------------
if __name__ == "__main__":
    with ThreadPoolExecutor() as ex:
        ex.map(process, BOROUGHS)
    print("✅ All oriented boroughs processed")

