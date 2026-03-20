"""
MYC3LIUM Mesh Analytics API Endpoints
Integrates mesh_graph_analyzer.py with FastAPI

Provides BloodHound-style queries + Maltego transforms
"""

import logging

from fastapi import APIRouter, HTTPException

from mesh_graph_analyzer import MeshGraphAnalyzer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mesh", tags=["mesh_analytics"])


# Global analyzer instance (refreshed per request)
def get_analyzer():
    """Get fresh mesh graph analyzer"""
    analyzer = MeshGraphAnalyzer()
    analyzer.build_graph()
    return analyzer


@router.get("/analytics/nodes_2_hops")
async def nodes_2_hops_away():
    """
    Find all nodes exactly 2 hops away from local node
    BloodHound-style query
    """
    analyzer = get_analyzer()

    if not analyzer.nodes:
        return []

    local_mac = next(iter(analyzer.nodes.keys()))
    nodes_2_hops = []

    for node_id in analyzer.nodes:
        if node_id == local_mac:
            continue

        path = analyzer.find_shortest_path(local_mac, node_id)
        if path and len(path) - 1 == 2:
            nodes_2_hops.append({"id": node_id, "path": path})

    return nodes_2_hops


@router.get("/analytics/critical_nodes")
async def get_critical_nodes():
    """
    Find articulation points (nodes whose removal partitions network)
    """
    analyzer = get_analyzer()
    critical = analyzer.find_critical_nodes()

    # Get centrality for each critical node
    centrality = analyzer.node_centrality()

    return [
        {
            "id": node_id,
            "centrality": centrality.get(node_id, 0),
            "reason": "Removal would partition network",
        }
        for node_id in critical
    ]


@router.get("/analytics/clusters")
async def get_isolated_clusters():
    """
    Find disconnected mesh components
    """
    analyzer = get_analyzer()
    clusters = analyzer.find_isolated_clusters()

    return {
        "num_clusters": len(clusters),
        "clusters": [
            {"id": f"cluster_{i}", "nodes": cluster, "size": len(cluster)}
            for i, cluster in enumerate(clusters)
        ],
    }


@router.get("/analytics/top_relays")
async def get_top_relays(limit: int = 5):
    """
    Get nodes with highest betweenness centrality (most traffic)
    """
    analyzer = get_analyzer()
    centrality = analyzer.node_centrality()

    sorted_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:limit]

    return [
        {
            "id": node_id,
            "centrality": score,
            "reason": f"Relays {int(score * 100)}% of shortest paths",
        }
        for node_id, score in sorted_nodes
    ]


@router.get("/analytics/path")
async def get_shortest_path(target: str):
    """
    Find shortest path from local node to target
    """
    analyzer = get_analyzer()

    if not analyzer.nodes:
        raise HTTPException(status_code=404, detail="No mesh nodes found")

    local_mac = next(iter(analyzer.nodes.keys()))

    if target not in analyzer.nodes:
        raise HTTPException(status_code=404, detail=f"Target node {target} not found")

    path = analyzer.find_shortest_path(local_mac, target)

    if not path:
        raise HTTPException(status_code=404, detail=f"No path to {target}")

    return {"source": local_mac, "target": target, "path": path, "hops": len(path) - 1}


@router.get("/analytics/stats")
async def get_network_stats():
    """
    Overall mesh network statistics
    """
    analyzer = get_analyzer()
    return analyzer.get_network_stats()


@router.get("/transforms/expand_node")
async def expand_node_transform(id: str):
    """
    Maltego-style transform: expand all entities related to a node
    """
    analyzer = get_analyzer()

    if id not in analyzer.nodes:
        raise HTTPException(status_code=404, detail=f"Node {id} not found")

    node = analyzer.nodes[id]

    # Find all related entities
    neighbors = list(analyzer.graph.neighbors(id))
    paths_to_critical = []

    for critical_id in analyzer.find_critical_nodes():
        path = analyzer.find_shortest_path(id, critical_id)
        if path:
            paths_to_critical.append(
                {"target": critical_id, "path": path, "hops": len(path) - 1}
            )

    return {
        "node": {
            "id": node.id,
            "mac": node.mac,
            "quality": node.link_quality,
            "interfaces": node.interfaces,
        },
        "neighbors": neighbors,
        "paths_to_critical": paths_to_critical,
        "centrality": analyzer.node_centrality().get(id, 0),
    }


@router.post("/search")
async def search_mesh(filters: dict):
    """
    Shodan-style search with filters

    Example filters:
    {
      "battery": {"operator": "<", "value": "30"},
      "radio": {"operator": "=", "value": "lora"}
    }
    """
    analyzer = get_analyzer()

    results = []

    for node_id, node in analyzer.nodes.items():
        match = True

        # Apply filters
        for key, filter_data in filters.items():
            operator = filter_data.get("operator", "=")
            value = filter_data.get("value")

            # Get node attribute
            node_value = getattr(node, key, None)

            if node_value is None:
                match = False
                break

            # Apply operator
            if operator == "<":
                if not (node_value < float(value)):
                    match = False
            elif operator == ">":
                if not (node_value > float(value)):
                    match = False
            elif operator == "=":
                if str(node_value) != str(value):
                    match = False

        if match:
            results.append(
                {
                    "id": node.id,
                    "mac": node.mac,
                    "quality": node.link_quality,
                    "last_seen": node.last_seen,
                }
            )

    return {"query": filters, "results": results, "count": len(results)}
