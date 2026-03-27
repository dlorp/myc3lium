#!/usr/bin/env python3
"""
OpenClaw Map-Reduce Helper Framework
Simplifies parallel batch operations with automatic agent spawning and result aggregation.
"""

import json
from pathlib import Path
from typing import List, Callable
from datetime import datetime

MEMORY_DIR = Path(__file__).parent

class MapReduceJob:
    """
    Coordinates parallel map-reduce operations across multiple agents.
    
    Usage:
        job = MapReduceJob(
            items=["topic1", "topic2", "topic3"],
            map_task="research this topic in depth",
            reduce_fn=lambda results: combine_markdown_reports(results)
        )
        final_result = job.execute()
    """
    
    def __init__(self, items: List, map_task: str, reduce_fn: Callable = None, agent_type: str = "research"):
        self.items = items
        self.map_task = map_task
        self.reduce_fn = reduce_fn or self._default_reduce
        self.agent_type = agent_type
        self.job_id = f"mapreduce-{int(datetime.now().timestamp())}"
        self.results = []
    
    def _default_reduce(self, results):
        """Default reduce: concatenate all results."""
        return "\n\n---\n\n".join(str(r) for r in results)
    
    def _spawn_agent(self, item, index):
        """
        Spawn agent for single item (map phase).
        In production, this would use sessions_spawn.
        """
        # Placeholder - actual implementation would call sessions_spawn
        task = f"{self.map_task}: {item}"
        
        return {
            "item": item,
            "index": index,
            "task": task,
            "agent_id": f"{self.job_id}-map-{index}",
            "status": "pending"
        }
    
    def execute_map(self):
        """Execute map phase (spawn agents for each item)."""
        print(f"\nMap-Reduce Job: {self.job_id}")
        print(f"Items: {len(self.items)}")
        print(f"Map task: {self.map_task}")
        print("\nMap phase:")
        
        map_jobs = []
        for i, item in enumerate(self.items):
            job = self._spawn_agent(item, i)
            map_jobs.append(job)
            print(f"  [{i+1}/{len(self.items)}] Spawned {job['agent_id']} for: {item}")
        
        return map_jobs
    
    def execute_reduce(self, map_results):
        """Execute reduce phase (aggregate results)."""
        print(f"\nReduce phase:")
        print(f"  Aggregating {len(map_results)} results...")
        
        final_result = self.reduce_fn(map_results)
        
        print(f"  ✓ Reduce complete")
        return final_result
    
    def execute(self):
        """Execute full map-reduce job."""
        # Map
        map_jobs = self.execute_map()
        
        # Simulate waiting for completion
        print("\n  Waiting for agents to complete...")
        
        # In production, would wait for agent completion events
        # For demo, simulate results
        map_results = [f"Result for {job['item']}" for job in map_jobs]
        
        # Reduce
        final_result = self.execute_reduce(map_results)
        
        return final_result

# Higher-level helpers

def parallel_research(topics: List[str], depth: str = "detailed"):
    """Research multiple topics in parallel."""
    job = MapReduceJob(
        items=topics,
        map_task=f"Research this topic with {depth} depth",
        reduce_fn=lambda results: {
            "summary": "\n\n".join(results),
            "topics_count": len(results)
        }
    )
    return job.execute()

def batch_analyze(files: List[str], analysis_type: str = "code review"):
    """Analyze multiple files in parallel."""
    job = MapReduceJob(
        items=files,
        map_task=f"Perform {analysis_type} on this file",
        reduce_fn=lambda results: {
            "analyses": results,
            "total_files": len(results)
        }
    )
    return job.execute()

def parallel_transform(items: List, transformation: str):
    """Apply transformation to items in parallel."""
    job = MapReduceJob(
        items=items,
        map_task=transformation,
        reduce_fn=lambda results: results  # Return as list
    )
    return job.execute()

# Example usage
if __name__ == '__main__':
    print("OpenClaw Map-Reduce Framework Demo")
    print("=" * 70)
    
    # Example 1: Research topics
    print("\nExample 1: Parallel research")
    print("-" * 70)
    topics = ["OpenAI API", "Anthropic Claude", "Google Gemini"]
    result = parallel_research(topics)
    print(f"\nFinal result preview:\n{str(result)[:200]}...")
    
    # Example 2: Custom map-reduce
    print("\n\nExample 2: Custom map-reduce")
    print("-" * 70)
    
    def custom_reduce(results):
        """Custom reduce: count total words."""
        total_words = sum(len(str(r).split()) for r in results)
        return {
            "results": results,
            "total_words": total_words,
            "avg_words": total_words // len(results) if results else 0
        }
    
    job = MapReduceJob(
        items=["doc1.md", "doc2.md", "doc3.md"],
        map_task="Summarize this document",
        reduce_fn=custom_reduce
    )
    
    result = job.execute()
    print(f"\nFinal result: {json.dumps(result, indent=2)}")
