/**
 * MYC3LIUM Mesh Analytics Hook
 * BloodHound-style analytics queries for P200 Lattice Map
 *
 * Uses existing data from BATMAN-adv + backend mesh_graph_analyzer.py
 */

import { useState, useEffect } from "react";

interface AnalyticsQuery {
  id: string;
  name: string;
  description: string;
  execute: () => Promise<unknown>;
}

export const useMeshAnalytics = () => {
  const [queries, setQueries] = useState<AnalyticsQuery[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // Initialize pre-built queries (like BloodHound)
    const builtInQueries: AnalyticsQuery[] = [
      {
        id: "nodes_1_hop",
        name: "Find All Nodes 1 Hop Away",
        description: "Direct neighbors of the local node",
        execute: async () => {
          const response = await fetch("/api/intelligence/topology");
          const data = await response.json();
          return data.nodes.filter(
            (n: { neighbors?: string[] }) =>
              n.neighbors && n.neighbors.includes("m3l_local")
          );
        },
      },
      {
        id: "nodes_2_hops",
        name: "Find All Nodes 2 Hops Away",
        description: "Nodes reachable via one intermediate relay",
        execute: async () => {
          const response = await fetch("/api/mesh/analytics/nodes_2_hops");
          return await response.json();
        },
      },
      {
        id: "critical_nodes",
        name: "Find Critical Relay Nodes",
        description: "Nodes whose removal would partition the network",
        execute: async () => {
          const response = await fetch("/api/mesh/analytics/critical_nodes");
          return await response.json();
        },
      },
      {
        id: "isolated_clusters",
        name: "Find Isolated Clusters",
        description: "Disconnected mesh segments",
        execute: async () => {
          const response = await fetch("/api/mesh/analytics/clusters");
          return await response.json();
        },
      },
      {
        id: "top_relays",
        name: "Find Top Relay Nodes",
        description: "Nodes with highest betweenness centrality (most traffic)",
        execute: async () => {
          const response = await fetch("/api/mesh/analytics/top_relays");
          return await response.json();
        },
      },
      {
        id: "shortest_path",
        name: "Find Shortest Path to Target",
        description: "Optimal route to a specific node",
        execute: async () => {
          // Would need target selection UI
          const target = prompt("Enter target node ID:");
          if (!target) return null;

          const response = await fetch(`/api/mesh/analytics/path?target=${target}`);
          return await response.json();
        },
      },
      {
        id: "weak_links",
        name: "Find Weak Links",
        description: "Links with RSSI < -90 dBm or quality < 100",
        execute: async () => {
          const response = await fetch("/api/intelligence/topology");
          const data = await response.json();

          return data.nodes.filter((n: { rssi?: number }) => n.rssi && n.rssi < -90);
        },
      },
      {
        id: "network_stats",
        name: "Get Network Statistics",
        description: "Overall mesh health metrics",
        execute: async () => {
          const response = await fetch("/api/mesh/analytics/stats");
          return await response.json();
        },
      },
    ];

    setQueries(builtInQueries);
  }, []);

  const executeQuery = async (queryId: string) => {
    setIsLoading(true);

    try {
      const query = queries.find((q) => q.id === queryId);
      if (!query) {
        throw new Error(`Query ${queryId} not found`);
      }

      const result = await query.execute();
      return result;
    } catch (error) {
      console.error(`Query ${queryId} failed:`, error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    queries,
    executeQuery,
    isLoading,
  };
};

/**
 * Maltego-style entity transforms
 * Click node → expand related entities
 */
export const useEntityTransforms = () => {
  const expandNode = async (nodeId: string) => {
    const response = await fetch(`/api/mesh/transforms/expand_node?id=${nodeId}`);
    return await response.json();
  };

  const expandObservations = async (nodeId: string) => {
    const response = await fetch(`/api/intelligence/observations?node=${nodeId}`);
    return await response.json();
  };

  const expandRFSources = async (nodeId: string) => {
    const response = await fetch(`/api/intelligence/rf_sources?detector=${nodeId}`);
    return await response.json();
  };

  return {
    expandNode,
    expandObservations,
    expandRFSources,
  };
};

/**
 * Search query parser (Shodan-style)
 * Examples:
 *   "battery:<30"
 *   "radio:lora AND distance:>5km"
 *   "services:camera"
 */
export const useMeshSearch = () => {
  const parseQuery = (query: string) => {
    const filters: Record<string, { operator: string; value: string }> = {};

    // Simple parser for key:value pairs
    const parts = query.split(" AND ");

    parts.forEach((part) => {
      const match = part.match(/(\w+):([<>]?)(.+)/);
      if (match) {
        const [, key, operator, value] = match;

        filters[key] = {
          operator: operator || "=",
          value: value.trim(),
        };
      }
    });

    return filters;
  };

  const searchMesh = async (query: string) => {
    const filters = parseQuery(query);

    const response = await fetch("/api/mesh/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filters }),
    });

    return await response.json();
  };

  return {
    parseQuery,
    searchMesh,
  };
};
