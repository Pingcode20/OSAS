import json

import networkx as nx
import matplotlib.pyplot as plt
import random
import util
import os
from definitions.paths import MAP_DIR
from pathlib import Path


class OSASMap:
    default_planet_names = 'KDL_PlanetNames.txt'

    p_edge_count = {
        1: 1,
        2: 0.9,
        3: 0.7,
        4: 0.15,
        5: 0.025,
        6: 0
    }  # probability of node having n-many edges

    map = nx.Graph()

    def __init__(self, map_name, default_planet_names='KDL_PlanetNames.txt'):
        self.map = nx.Graph(map_name=map_name)
        self.default_planet_names = default_planet_names

    def generate_names(self, nodes, planet_names=None):
        if planet_names is None:
            planet_names = self.default_planet_names

        # Load name list
        planet_name_file = Path(__file__).parent / "planetnames" / planet_names
        f = open(planet_name_file, encoding='utf-8-sig')
        planet_names = {name.strip() for name in f.readlines()}

        # Filter out already-used names
        used_names = set(self.map.nodes)
        unused_names = list(planet_names - used_names)

        random.shuffle(unused_names)

        return {k: v for k, v in zip(nodes, unused_names[0:len(nodes)])}

    def generate_linked_graph(self, node_count, max_links, centre=[0, 0], radius=10, planet_names=None):
        # Generate a regular graph with maximum possible links for every node
        G = nx.random_regular_graph(max_links, node_count)
        planet_names = self.generate_names(G.nodes, planet_names)
        G = nx.relabel_nodes(G, planet_names)

        # Identify a minimum spanning tree to ensure all nodes are connected - these links can't be trimmed
        mst = [edge[0:2] for edge in nx.algorithms.tree.mst.minimum_spanning_edges(G)]
        mst_unordered = mst + [(y, x) for x, y in mst]

        # Loop through each node and randomly trim excess linkages
        for node in G.nodes:
            edges = G.edges(node)
            edge_count = len(edges)
            removable_edges = [edge for edge in edges if edge not in mst_unordered]
            random.shuffle(removable_edges)
            for edge in removable_edges:
                if random.random() > self.p_edge_count[edge_count]:
                    G.remove_edge(*edge)
                    edge_count -= 1

        # Spring to adjust locations
        layout = nx.spring_layout(G, k=0.4, iterations=50)
        pos = nx.rescale_layout_dict(layout, radius)

        for n in pos:
            pos[n] = [pos[n][0] + centre[0], pos[n][1] + centre[1]]

        nx.set_node_attributes(G, pos, name='pos')

        self.map = nx.compose(self.map, G)

    def generate_unlinked_nodes(self, node_count, centre=[0, 0], radius_outer=10, radius_inner=0, planet_names=None):
        G = nx.Graph()
        G.add_nodes_from(range(0, node_count))

        planet_names = self.generate_names(G.nodes, planet_names)
        G = nx.relabel_nodes(G, planet_names)

        layout = nx.random_layout(G)
        pos_scaled = nx.rescale_layout_dict(layout, radius_outer)

        for node in pos_scaled:
            pos_initial = pos_scaled[node]
            pos_shifted = [sum(x) for x in zip(pos_initial, centre)]
            pos_polar = util.rect2pol(*pos_shifted)
            radius = pos_polar[0] + radius_inner
            pos_polar_final = [radius, pos_polar[1]]
            pos_rect = util.pol2rect(*pos_polar_final)

            G.nodes[node]['pos'] = pos_rect

        self.map = nx.compose(self.map, G)

    # Bump close nodes away from each other
    def bump_close_nodes(self, min_distance: float):
        for node_a in self.map.nodes:
            pos_a = self.map.nodes[node_a]['pos']
            other_nodes = {n: self.map.nodes[n]['pos'] for n in self.map.nodes if n is not node_a}

            for node_b in other_nodes:
                pos_b = other_nodes[node_b]
                r, theta = util.rect_vector(pos_a, pos_b)
                # If nodes are too close, bump them to the minimum distance
                if r < min_distance:
                    delta_x, delta_y = util.pol2rect(min_distance / 2, theta)
                    self.map.nodes[node_a]['pos'] = [pos_a[0] - delta_x, pos_a[1] - delta_y]
                    self.map.nodes[node_b]['pos'] = [pos_b[0] + delta_x, pos_b[1] + delta_y]

    def show(self):
        plot = plt.figure(figsize=(20, 20))
        nx.draw(self.map, nx.get_node_attributes(self.map, 'pos'), with_labels=True)

        plot.show_line()

    def save(self):
        map_name = self.map.graph['map_name']
        map_data = nx.node_link_data(self.map)

        filename = os.path.join(MAP_DIR, map_name + '.json')
        f = open(filename, mode='w')
        json.dump(map_data, f)
        f.close()

    def load(self):
        map_name = self.map.graph['map_name']

        filename = os.path.join(MAP_DIR, map_name + '.json')
        f = open(filename, mode='r')
        map_data = json.load(f)
        f.close()

        self.map = nx.node_link_graph(map_data)
        return self


if __name__ == '__main__':
    game_map = OSASMap(map_name='test')

    game_map.generate_linked_graph(30, 6, radius=10)
    game_map.generate_unlinked_nodes(80, radius_inner=6, radius_outer=10)
    game_map.bump_close_nodes(0.5)

    game_map.show()

    # game_map.save()
