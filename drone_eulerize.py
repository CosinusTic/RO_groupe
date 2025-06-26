import osmnx as ox
import networkx as nx
import pickle
import os

# Configuration
place = "Plateau-Mont-Royal, Montréal, Québec, Canada"
output_dir = "resources"
output_file = os.path.join(output_dir, "eulerized_montreal_graph.pkl")

print("Chargement du réseau routier de Montréal...")
G = ox.graph_from_place(place, network_type='drive', simplify=True, retain_all=False)

# Convertir en graphe non orienté
G_undirected = G.to_undirected()

# Identifier les noeuds de degré impair
odd_degree_nodes = [node for node, degree in G_undirected.degree() if degree % 2 == 1]
print(f"{len(odd_degree_nodes)} noeuds de degré impair trouvés")

# Euleriser le graphe
print("Eulerisation du graphe...")
G_eulerized = nx.eulerize(G_undirected)

# Vérifier que le graphe est maintenant eulérien
is_eulerian = nx.is_eulerian(G_eulerized)
print("Graphe eulérien:", is_eulerian)

# Créer le dossier de sortie si nécessaire
os.makedirs(output_dir, exist_ok=True)

# Sauvegarder le graphe eulérisé
with open(output_file, 'wb') as f:
    pickle.dump(G_eulerized, f)

print(f"Graphe eulérisé sauvegardé dans: {output_file}")

