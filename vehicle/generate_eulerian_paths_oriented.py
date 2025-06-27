#!/usr/bin/env python3
import os, json, pickle, networkx as nx, osmnx as ox, matplotlib.pyplot as plt
from concurrent.futures import ThreadPoolExecutor
from slugify import slugify

BOROUGHS = [
    "Plateau-Mont-Royal, Montréal, Québec, Canada",
    "Outremont, Montréal, Québec, Canada",
    "Verdun, Montréal, Québec, Canada",
    "Anjou, Montréal, Québec, Canada",
    "Rivière-des-Prairies–Pointe-aux-Trembles, Montréal, Québec, Canada"
]

OUT_ROOT = "resources/neighborhoods"
os.makedirs(OUT_ROOT, exist_ok=True)

def directed_walk_from_undirected_circuit(G_dir, circuit):
    """Turn undirected Eulerian edges into a directed legal walk."""
    walk = []
    for u, v in circuit:
        if G_dir.has_edge(u, v):                # legal direction
            walk.append((u, v))
        elif G_dir.has_edge(v, u):              # need reverse path
            try:
                sp = nx.shortest_path(G_dir, u, v, weight="length")
            except nx.NetworkXNoPath:
                sp = None
            if sp and len(sp) > 1:
                walk.extend([(sp[i], sp[i+1]) for i in range(len(sp)-1)])
            else:                               # fallback: add reverse edge anyway
                walk.append((v, u))
        else:
            walk.append((u, v))                 # edge vanished - just keep it
    return walk

def process(place):
    slug = slugify(place.split(",")[0])
    n_dir  = os.path.join(OUT_ROOT, slug)
    os.makedirs(n_dir, exist_ok=True)

    print(f"[{slug}] downloading directed graph…")
    G_dir = ox.graph_from_place(place, network_type="drive", simplify=True, retain_all=False)
    with open(os.path.join(n_dir,"raw_graph_oriented.pkl"),"wb") as f: pickle.dump(G_dir,f)

    # Undirected eulerization
    G_un  = G_dir.to_undirected()
    G_eu  = nx.eulerize(G_un)
    circuit = list(nx.eulerian_circuit(G_eu))
    with open(os.path.join(n_dir,"eulerized_graph_oriented.pkl"),"wb") as f: pickle.dump(G_eu,f)

    # Convert circuit into a legal directed walk
    walk = directed_walk_from_undirected_circuit(G_dir, circuit)
    with open(os.path.join(n_dir,"eulerian_path_oriented.json"),"w") as f:
        json.dump([{"u":u,"v":v} for u,v in walk], f, indent=2)

    # Quick diagnostic plot (optional)
    fig, ax = ox.plot_graph(G_dir, show=False, close=False,
                            edge_color="lightgray", node_size=0, bgcolor="white")
    xs, ys = [], []
    for u, v in walk:
        xs += [G_dir.nodes[u]['x'], G_dir.nodes[v]['x']]
        ys += [G_dir.nodes[u]['y'], G_dir.nodes[v]['y']]
    ax.plot(xs, ys, color="red", linewidth=1, alpha=0.7)
    plt.savefig(os.path.join(n_dir,"path_visualization_oriented.png"), dpi=300)
    plt.close(fig)
    print(f"[{slug}] ✔ oriented walk saved ({len(walk)} segments)")

if __name__ == "__main__":
    with ThreadPoolExecutor() as exe:
        exe.map(process, BOROUGHS)
    print("✅ All oriented boroughs processed")

