"""
MYC3LIUM Mesh Graph Analyzer
BloodHound-style topology analysis for mesh networks

Analyzes BATMAN-adv mesh to find:
- Shortest paths between nodes
- Critical relay points (if removed, network partitions)
- Isolated clusters
- Link quality metrics
"""

import json
import logging
import re
import subprocess
from dataclasses import dataclass
from typing import Optional

import networkx as nx

logger = logging.getLogger(__name__)


@dataclass
class MeshNode:
    """Mesh network node"""
    id: str
    mac: str
    last_seen: float  # seconds ago
    link_quality: int  # 0-255
    interfaces: list[str]  # ['lora0', 'wlan1', 'wlan0']


@dataclass
class MeshLink:
    """Link between two nodes"""
    source: str
    target: str
    interface: str  # Which radio carries this link
    quality: int  # 0-255
    rssi: Optional[float]  # dBm
    bandwidth: Optional[float]  # Mbps estimate


class MeshGraphAnalyzer:
    """
    Analyze mesh topology like BloodHound analyzes Active Directory
    """

    def __init__(self):
        self.graph = nx.DiGraph()
        self.nodes: dict[str, MeshNode] = {}
        self.links: list[MeshLink] = []

    def query_batman_neighbors(self) -> list[dict]:
        """
        Query BATMAN-adv for current neighbors
        """
        try:
            result = subprocess.run(
                ['batctl', 'n'],
                capture_output=True,
                text=True,
                timeout=5
            )

            neighbors = []

            # Parse: "aa:bb:cc:dd:ee:ff  0.123s (255) [wlan0]"
            pattern = r'([0-9a-f:]+)\s+([0-9.]+)s\s+\((\d+)\)\s+\[(.+?)\]'

            for line in result.stdout.split('\n'):
                match = re.search(pattern, line)
                if match:
                    mac, last_seen, quality, interface = match.groups()
                    neighbors.append({
                        'mac': mac,
                        'last_seen': float(last_seen),
                        'quality': int(quality),
                        'interface': interface
                    })

            return neighbors

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.error(f"BATMAN query failed: {e}")
            return []

    def query_batman_originators(self) -> list[dict]:
        """
        Query all mesh originators (all nodes in mesh)
        """
        try:
            result = subprocess.run(
                ['batctl', 'o'],
                capture_output=True,
                text=True,
                timeout=5
            )

            originators = []

            # Parse originator table
            for line in result.stdout.split('\n'):
                if re.match(r'[0-9a-f:]+', line):
                    parts = line.split()
                    if len(parts) >= 4:
                        originators.append({
                            'mac': parts[0],
                            'last_seen': parts[1],
                            'quality': int(parts[2].strip('()')),
                            'next_hop': parts[3]
                        })

            return originators

        except Exception as e:
            logger.error(f"Originator query failed: {e}")
            return []

    def build_graph(self):
        """
        Build NetworkX graph from BATMAN data
        """
        self.graph.clear()
        self.nodes.clear()
        self.links.clear()

        # Get local node MAC
        try:
            local_mac = open('/sys/class/net/bat0/address').read().strip()
        except:
            local_mac = "00:00:00:00:00:00"

        # Add local node
        self.graph.add_node(local_mac, label="LOCAL")
        self.nodes[local_mac] = MeshNode(
            id=local_mac,
            mac=local_mac,
            last_seen=0.0,
            link_quality=255,
            interfaces=['bat0']
        )

        # Add neighbors
        neighbors = self.query_batman_neighbors()

        for neighbor in neighbors:
            mac = neighbor['mac']

            if mac not in self.graph:
                self.graph.add_node(mac, label=mac[-8:])
                self.nodes[mac] = MeshNode(
                    id=mac,
                    mac=mac,
                    last_seen=neighbor['last_seen'],
                    link_quality=neighbor['quality'],
                    interfaces=[neighbor['interface']]
                )

            # Add edge
            self.graph.add_edge(
                local_mac,
                mac,
                weight=255 - neighbor['quality'],  # Lower quality = higher weight
                interface=neighbor['interface'],
                quality=neighbor['quality']
            )

            self.links.append(MeshLink(
                source=local_mac,
                target=mac,
                interface=neighbor['interface'],
                quality=neighbor['quality'],
                rssi=None,
                bandwidth=None
            ))

    def find_shortest_path(self, source: str, target: str) -> Optional[list[str]]:
        """
        Find shortest path between two nodes (like BloodHound's path queries)
        """
        try:
            path = nx.shortest_path(self.graph, source, target, weight='weight')
            return path
        except nx.NetworkXNoPath:
            return None

    def find_all_paths(self, source: str, target: str, cutoff: int = 5) -> list[list[str]]:
        """
        Find all paths up to cutoff length
        """
        try:
            paths = list(nx.all_simple_paths(self.graph, source, target, cutoff=cutoff))
            return paths
        except nx.NetworkXNoPath:
            return []

    def find_critical_nodes(self) -> list[str]:
        """
        Find articulation points (nodes whose removal disconnects the network)
        Like finding Domain Admins in BloodHound
        """
        # Convert to undirected for articulation points
        undirected = self.graph.to_undirected()
        articulation_points = list(nx.articulation_points(undirected))

        return articulation_points

    def find_isolated_clusters(self) -> list[list[str]]:
        """
        Find disconnected components (isolated mesh clusters)
        """
        undirected = self.graph.to_undirected()
        components = list(nx.connected_components(undirected))

        return [list(component) for component in components]

    def node_centrality(self) -> dict[str, float]:
        """
        Calculate betweenness centrality (how often a node is on shortest paths)
        High centrality = critical relay node
        """
        centrality = nx.betweenness_centrality(self.graph)
        return centrality

    def get_network_stats(self) -> dict:
        """
        Overall network statistics
        """
        undirected = self.graph.to_undirected()

        stats = {
            'total_nodes': self.graph.number_of_nodes(),
            'total_links': self.graph.number_of_edges(),
            'network_diameter': nx.diameter(undirected) if nx.is_connected(undirected) else None,
            'average_degree': sum(dict(self.graph.degree()).values()) / self.graph.number_of_nodes() if self.graph.number_of_nodes() > 0 else 0,
            'connected': nx.is_connected(undirected),
            'num_components': nx.number_connected_components(undirected)
        }

        return stats

    def export_cytoscape_json(self) -> dict:
        """
        Export graph in Cytoscape.js format (for P200 visualization)
        """
        elements = []

        # Nodes
        for node_id, node in self.nodes.items():
            elements.append({
                'data': {
                    'id': node_id,
                    'label': node_id[-8:],
                    'quality': node.link_quality,
                    'interfaces': ','.join(node.interfaces)
                }
            })

        # Edges
        for link in self.links:
            elements.append({
                'data': {
                    'source': link.source,
                    'target': link.target,
                    'interface': link.interface,
                    'quality': link.quality
                }
            })

        return {'elements': elements}

    def run_prebuilt_queries(self) -> dict:
        """
        Run BloodHound-style pre-built analytics queries
        """
        queries = {}

        # Query 1: Find all nodes N hops away
        local_mac = next(iter(self.nodes.keys())) if self.nodes else None
        if local_mac:
            for n in [1, 2, 3]:
                nodes_n_hops = []
                for node in self.nodes:
                    try:
                        path = nx.shortest_path(self.graph, local_mac, node)
                        if len(path) - 1 == n:
                            nodes_n_hops.append(node)
                    except nx.NetworkXNoPath:
                        pass

                queries[f'nodes_{n}_hops_away'] = nodes_n_hops

        # Query 2: Find critical relay nodes
        queries['critical_nodes'] = self.find_critical_nodes()

        # Query 3: Find isolated clusters
        queries['isolated_clusters'] = self.find_isolated_clusters()

        # Query 4: Node centrality rankings
        centrality = self.node_centrality()
        sorted_centrality = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
        queries['top_relay_nodes'] = [{'node': k, 'centrality': v} for k, v in sorted_centrality[:5]]

        # Query 5: Network statistics
        queries['network_stats'] = self.get_network_stats()

        return queries


# FastAPI endpoint integration
async def get_mesh_graph_analysis():
    """
    API endpoint for mesh graph analysis
    """
    analyzer = MeshGraphAnalyzer()
    analyzer.build_graph()

    queries = analyzer.run_prebuilt_queries()
    cytoscape_data = analyzer.export_cytoscape_json()

    return {
        'graph': cytoscape_data,
        'analytics': queries
    }


if __name__ == "__main__":
    # Test analyzer
    logging.basicConfig(level=logging.INFO)

    analyzer = MeshGraphAnalyzer()
    analyzer.build_graph()

    print("=== MESH GRAPH ANALYSIS ===\n")

    queries = analyzer.run_prebuilt_queries()

    print(f"Total Nodes: {queries['network_stats']['total_nodes']}")
    print(f"Total Links: {queries['network_stats']['total_links']}")
    print(f"Connected: {queries['network_stats']['connected']}")
    print(f"Network Diameter: {queries['network_stats']['network_diameter']}")

    print("\nCritical Nodes (if removed, network partitions):")
    for node in queries['critical_nodes']:
        print(f"  - {node}")

    print("\nTop Relay Nodes (by centrality):")
    for item in queries['top_relay_nodes']:
        print(f"  - {item['node']}: {item['centrality']:.3f}")

    print("\nCytoscape JSON:")
    print(json.dumps(analyzer.export_cytoscape_json(), indent=2))
