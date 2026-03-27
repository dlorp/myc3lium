#!/usr/bin/env python3
"""
OpenClaw Hierarchical Health Aggregation
Roll-up health from components → subsystems → overall system health.
"""

import json
from pathlib import Path
from datetime import datetime
from enum import Enum

MEMORY_DIR = Path(__file__).parent
HEALTH_FILE = MEMORY_DIR / "agent-health.json"

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class HealthAggregator:
    def __init__(self):
        self.health_file = HEALTH_FILE
    
    def load_health(self):
        """Load current health data."""
        if self.health_file.exists():
            with open(self.health_file) as f:
                return json.load(f)
        return None
    
    def aggregate_component(self, component_data):
        """Aggregate health for a single component."""
        status = component_data.get('status', 'unknown')
        
        if status == 'ok' or status == 'healthy':
            return HealthStatus.HEALTHY
        elif status == 'warning' or status == 'degraded':
            return HealthStatus.DEGRADED
        elif status == 'error' or status == 'critical':
            return HealthStatus.CRITICAL
        else:
            return HealthStatus.UNKNOWN
    
    def aggregate_subsystem(self, components):
        """
        Aggregate health for subsystem from components.
        Rules:
        - Any CRITICAL component → subsystem CRITICAL
        - Any DEGRADED component → subsystem DEGRADED
        - All HEALTHY → subsystem HEALTHY
        - All UNKNOWN → subsystem UNKNOWN
        """
        statuses = [self.aggregate_component(c) for c in components.values()]
        
        if HealthStatus.CRITICAL in statuses:
            return HealthStatus.CRITICAL
        elif HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        elif all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY
        elif all(s == HealthStatus.UNKNOWN for s in statuses):
            return HealthStatus.UNKNOWN
        else:
            return HealthStatus.DEGRADED
    
    def aggregate_overall(self):
        """Aggregate overall system health."""
        health = self.load_health()
        if not health:
            return None
        
        # Build hierarchy
        hierarchy = {
            "Overall Health": {
                "Memory Subsystem": {
                    "MEMORY.md loaded": health.get('selfDiagnostic', {}).get('memoryFiles', {}).get('MEMORY.md', False),
                    "SOUL.md loaded": health.get('selfDiagnostic', {}).get('memoryFiles', {}).get('SOUL.md', False),
                    "AGENTS.md loaded": health.get('selfDiagnostic', {}).get('memoryFiles', {}).get('AGENTS.md', False)
                },
                "Agent Subsystem": {
                    "Active agents": {"status": "ok" if health.get('cognitiveCapacity', {}).get('activeTasks', 0) < 8 else "warning"},
                    "Token utilization": {"status": "ok" if health.get('cognitiveCapacity', {}).get('utilizationPercent', 0) < 80 else "degraded"}
                },
                "External Dependencies": health.get('dependencies', {})
            }
        }
        
        # Aggregate each subsystem
        results = {}
        
        # Memory subsystem
        memory_components = {
            k: {"status": "ok" if v else "error"}
            for k, v in health.get('selfDiagnostic', {}).get('memoryFiles', {}).items()
        }
        memory_health = self.aggregate_subsystem(memory_components)
        results["Memory Subsystem"] = memory_health
        
        # Agent subsystem
        agent_components = {
            "Active agents": {"status": "ok" if health.get('cognitiveCapacity', {}).get('activeTasks', 0) < 8 else "warning"},
            "Token utilization": {"status": "ok" if health.get('cognitiveCapacity', {}).get('utilizationPercent', 0) < 80 else "degraded"}
        }
        agent_health = self.aggregate_subsystem(agent_components)
        results["Agent Subsystem"] = agent_health
        
        # External dependencies
        deps = health.get('dependencies', {})
        deps_health = self.aggregate_subsystem(deps)
        results["External Dependencies"] = deps_health
        
        # Overall
        overall_health = self.aggregate_subsystem({
            "memory": {"status": memory_health.value},
            "agents": {"status": agent_health.value},
            "deps": {"status": deps_health.value}
        })
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall": overall_health.value,
            "subsystems": {k: v.value for k, v in results.items()},
            "hierarchy": hierarchy
        }
    
    def visualize(self):
        """Visualize hierarchical health."""
        aggregated = self.aggregate_overall()
        if not aggregated:
            print("No health data available")
            return
        
        overall = aggregated['overall']
        subsystems = aggregated['subsystems']
        
        # Map status to emoji
        emoji = {
            "healthy": "✅",
            "degraded": "⚠️",
            "critical": "🔴",
            "unknown": "❓"
        }
        
        print("\nHierarchical Health Status")
        print("=" * 70)
        print(f"\nOverall Health: {emoji.get(overall, '?')} {overall.upper()}")
        print("\nSubsystems:")
        
        for name, status in subsystems.items():
            print(f"  {emoji.get(status, '?')} {name}: {status}")
        
        print()
        
        # Root cause if degraded
        if overall != "healthy":
            print("Root Cause Analysis:")
            for name, status in subsystems.items():
                if status in ["degraded", "critical"]:
                    print(f"  → {name} is {status}")

# CLI
if __name__ == '__main__':
    aggregator = HealthAggregator()
    aggregator.visualize()
