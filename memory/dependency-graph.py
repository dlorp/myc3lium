#!/usr/bin/env python3
"""
OpenClaw Dependency Graph Tracker
Detects circular dependencies and deadlocks in multi-agent workflows.
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict, deque

MEMORY_DIR = Path(__file__).parent
GRAPH_FILE = MEMORY_DIR / "dependency-graph.json"

class DependencyGraph:
    def __init__(self):
        self.graph_file = GRAPH_FILE
        self._load()
    
    def _load(self):
        """Load graph from file."""
        if self.graph_file.exists():
            with open(self.graph_file) as f:
                self.data = json.load(f)
        else:
            self.data = {
                "nodes": {},  # agentId -> metadata
                "edges": {},  # agentId -> [blocked_by_agents]
                "events": []
            }
            self._save()
    
    def _save(self):
        """Save graph to file."""
        with open(self.graph_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def add_node(self, agent_id: str, metadata: dict = None):
        """Add agent node to graph."""
        self.data['nodes'][agent_id] = {
            "addedAt": datetime.now().isoformat(),
            "metadata": metadata or {},
            "status": "active"
        }
        self.data['edges'][agent_id] = []
        self._save()
    
    def add_dependency(self, agent_id: str, blocked_by: str):
        """Add dependency: agent_id is blocked by blocked_by."""
        if agent_id not in self.data['edges']:
            self.add_node(agent_id)
        if blocked_by not in self.data['edges']:
            self.add_node(blocked_by)
        
        if blocked_by not in self.data['edges'][agent_id]:
            self.data['edges'][agent_id].append(blocked_by)
        
        # Log event
        self.data['events'].append({
            "timestamp": datetime.now().isoformat(),
            "type": "dependency_added",
            "agent": agent_id,
            "blockedBy": blocked_by
        })
        
        self._save()
        
        # Check for cycles
        if self.detect_cycle():
            print(f"⚠️  Circular dependency detected!")
            return False
        
        return True
    
    def remove_dependency(self, agent_id: str, blocked_by: str):
        """Remove dependency."""
        if agent_id in self.data['edges'] and blocked_by in self.data['edges'][agent_id]:
            self.data['edges'][agent_id].remove(blocked_by)
            self._save()
    
    def mark_completed(self, agent_id: str):
        """Mark agent as completed (unblock dependents)."""
        if agent_id in self.data['nodes']:
            self.data['nodes'][agent_id]['status'] = 'completed'
            self.data['nodes'][agent_id]['completedAt'] = datetime.now().isoformat()
        
        # Remove this agent from all dependency lists
        for deps in self.data['edges'].values():
            if agent_id in deps:
                deps.remove(agent_id)
        
        self._save()
    
    def detect_cycle(self):
        """
        Detect circular dependencies using DFS.
        Returns list of agents in cycle, or None if no cycle.
        """
        # Build adjacency list
        graph = self.data['edges']
        
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(node):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    # Cycle found
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:]
            
            path.pop()
            rec_stack.remove(node)
            return False
        
        for node in graph:
            if node not in visited:
                cycle = dfs(node)
                if cycle:
                    return cycle
        
        return None
    
    def visualize(self):
        """Visualize dependency graph."""
        print("\nDependency Graph")
        print("=" * 70)
        
        for agent, deps in self.data['edges'].items():
            status = self.data['nodes'].get(agent, {}).get('status', 'unknown')
            
            if deps:
                print(f"{agent} [{status}]")
                for dep in deps:
                    dep_status = self.data['nodes'].get(dep, {}).get('status', 'unknown')
                    print(f"  ↳ blocked by: {dep} [{dep_status}]")
            else:
                print(f"{agent} [{status}] (no dependencies)")
        
        print()
        
        # Check for cycles
        cycle = self.detect_cycle()
        if cycle:
            print("⚠️  CIRCULAR DEPENDENCY DETECTED!")
            if isinstance(cycle, list):
                print("   Cycle: " + " → ".join(cycle))
            else:
                print("   Cycle detected in graph")
            print("   Action: Kill one of these agents to break deadlock")
        else:
            print("✓ No circular dependencies")

# CLI interface
if __name__ == '__main__':
    import sys
    
    graph = DependencyGraph()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  dependency-graph.py add <agent>")
        print("  dependency-graph.py depend <agent> <blocked-by>")
        print("  dependency-graph.py complete <agent>")
        print("  dependency-graph.py visualize")
        print("  dependency-graph.py demo")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'add':
        agent = sys.argv[2]
        graph.add_node(agent)
        print(f"✓ Added {agent}")
    
    elif cmd == 'depend':
        agent = sys.argv[2]
        blocked_by = sys.argv[3]
        graph.add_dependency(agent, blocked_by)
    
    elif cmd == 'complete':
        agent = sys.argv[2]
        graph.mark_completed(agent)
        print(f"✓ Marked {agent} as completed")
    
    elif cmd == 'visualize':
        graph.visualize()
    
    elif cmd == 'demo':
        # Demo: Create circular dependency
        print("Creating dependency graph with circular dependency...\n")
        graph.add_node("agent-A")
        graph.add_node("agent-B")
        graph.add_node("agent-C")
        
        graph.add_dependency("agent-A", "agent-B")
        graph.add_dependency("agent-B", "agent-C")
        graph.add_dependency("agent-C", "agent-A")  # Creates cycle!
        
        graph.visualize()
