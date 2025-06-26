import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt

print("Chargement du réseau routier de Montréal...")
place = "Plateau-Mont-Royal, Montréal, Québec, Canada"
G = ox.graph_from_place(place, network_type='drive', simplify=True, retain_all=False)

# Convertir en graphe non orienté
G_undirected = G.to_undirected()

# Vérifier les noeuds impairs
odd_degree_nodes = [node for node, degree in G_undirected.degree() if degree % 2 == 1]
print(f"{len(odd_degree_nodes)} noeuds de degré impair trouvés")

# Euleriser le graphe
G_eulerized = nx.eulerize(G_undirected)

# Calculer le circuit eulérien
euler_circuit = list(nx.eulerian_circuit(G_eulerized))

# Extraire les coordonnées des points du chemin
route_nodes = [u for u, v in euler_circuit] + [euler_circuit[-1][1]]  # ajouter le dernier point
route_coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in route_nodes]

# Tracer le graphe avec OSMnx
fig, ax = ox.plot_graph(G_undirected, show=False, close=False, edge_color='lightgray', node_size=0, bgcolor='white')

# Tracer le chemin eulérien en rouge par-dessus
lats, lons = zip(*route_coords)
ax.plot(lons, lats, color='red', linewidth=1.5, alpha=0.7)

# Titre et affichage
ax.set_title("Chemin eulérien approximatif sur Montréal", fontsize=12)


print("Generation strategy:\n1. Generate png (ideal for non-interactive environments)\n2. Display straight away\n")
choice = input("Your choice: ")

if choice == 1 or choice == '1':
    plt.savefig("resources/eulerian_path_montreal.png", dpi=300)
    print("Saved to resources/eulerian_path_montreal.png")
else:
    plt.show()
